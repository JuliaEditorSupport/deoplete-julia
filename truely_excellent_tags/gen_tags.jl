kinds = Dict("module"=>"p",
			 "macro"=>"d", 
			 "variable"=>"v",
			 "function"=>"f"
			 )

immutable Tag
	name::AbstractString
	file::AbstractString
	address::AbstractString
	fields::Dict{AbstractString,AbstractString}
end


"""
http://ctags.sourceforge.net/FORMAT
{tagname}<Tab>{tagfile}<Tab>{tagaddress}[;"<Tab>{tagfield}..]

   {tagname}	Any identifier, not containing white space..
   <Tab>	Exactly one TAB character (although many versions of Vi can
		handle any amount of white space).
   {tagfile}	The name of the file where {tagname} is defined, relative to
   		the current directory (or location of the tags file?).
   {tagaddress}	Any Ex command.  When executed, it behaves like 'magic' was
		not set.  It may be restricted to a line number or a search
		pattern (Posix).
Optionally:
   ;"		semicolon + doublequote: Ends the tagaddress in way that looks
		like the start of a comment to Vi.
   {tagfield}	See below. 

"""
function write_tag(fp::IO, tag::Tag)
	tag.fields["language"]="julia"

	print(fp, "$(tag.name)\t$(tag.file)\t$(tag.address);\"")
	for (field,value) in tag.fields
		print(fp,"\t$field:$value")
	end
	println(fp)
end

function tags_function_like(name, mm::Module, value)
	Task() do 
		mt=methods(value) 
		mtdef = mt.defs
			
		while mtdef|>typeof == TypeMapEntry #TODO Latest reflection.jl adds code to convert the MethodsTable to a arraylike MethodsList. So this can be written as a for-loop
			#Cycle through the linked list while we get a link
			println("*$mtdef")
			func = mtdef.func
			if mm!=func.module 
				continue #Skip things from other modules (including submodules) 
			end

			fields = Dict{AbstractString,AbstractString}()
			fields["module"]= mm|>string
			file = func.file |> string |> Base.find_source_file
			address = func.line |> string
			
			args = map(string, mtdef.sig.parameters[2:end])
			fields["arity"] = string(length(args))
			fields["args"] = join(args,",")
			produce(Tag(name,file,address,fields))
		
			mtdef = mtdef.next
		end
	end
end

function tags_macro(name, mm::Module,  value::Function)
	Task() do
		for tag in tags_function_like(name,mm,value)
			tag.fields["kind"] = kinds["module"]
			produce(tag)
		end
	end
end


function tags(name_sym::Symbol, mm::Module,  value::Function)
	name=string(name_sym)
	Task() do
		for tag in tags_function_like(name,mm,value)
			tag.fields["kind"] = kinds["function"]
			produce(tag)
		end
	end
end

function tags(name_sym::Symbol,mm::Module, tt::Type)
	name=string(name_sym)
	Task() do
		filename = module_to_filename(mm) 
			#This is a bad attempt But it is what we got right now
		type_fields = ["$fname::"*string(fieldtype(tt,fname)) for fname in fieldnames(tt)]
		fields=Dict("kind"  => kinds["type"],
					"module"=> string(mm),
					"fields"=>	join(",", type_fields),
					"other_type_parameters"=>join(",",map(string,
														  setdiff(tt.parameters,tt.types))),
					"abstract"=> tt.abstract,
					"mutable"=> tt.mutable,
					"size"=> tt.size,
					"supertype"=>sypertype(tt),
					"bitstype"=>isbits(tt)
					)
		produce(Tag(name,r"/^[typealias|type|abstract|immutable]\s+name\s*=/",
					filename,fields))

	end	
end

function module_to_filename(mm::Module)
	name = mm==Base ? "sysimg" : mm==Core ? "coreimg": string(mm)
	Base.find_source_file(name*".jl")
end

function tags(name_sym::Symbol,mm::Module, submodule::Module)
	name=string(name_sym)
	Task() do 
		filename = module_to_filename(submodule)
		fields=Dict("kind"  => kinds["module"],
					"module"=> module_parent(mm)
					)
		produce(Tag(name,r"/^module name/",filename,fields))
	end
end


function tags(name_sym::Symbol,mm::Module, variable::Any)
	name=string(name_sym)
	if first(name)=='@'
		tags_macro(name,mm,variable)
	else
		Task() do
			filename=module_to_filename(mm) 
				#This is a bad attempt But it is what we got right now
				#Accessing variables from modules is a bad idea anyway
			fields=Dict("kind"  => kinds["variable"],
						"module"=> string(mm),
						"type"  => string(typeof(variable)),
						"constant" => string(isconst(mm,name_sym)),
						)
			produce(Tag(name,r"/name\s*=/",filename,fields))	
		end
	end	
end

function tags_from_module(mm::Module)

	Task() do 
		for name_sym in names(mm)
			value = eval(mm,name_sym)
			map(produce, tags(name_sym, mm,  value))
		end
	end
end


for tag in tags_from_module(Base)
	write_tag(STDOUT,tag) 

end

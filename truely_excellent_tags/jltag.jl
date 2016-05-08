kinds = Dict("module"=>"p",
			 "variable"=>"v",
			 "function"=>"f",
			 "datatype"=>"s",
			 "union"=>"u",
			 "type" =>"t"
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



function tags(name_sym::Symbol, mm::Module,  value::Function)
	name=string(name_sym)
	Task() do
		for func in Base.MethodList(methods(value))
			if mm!=func.module 
				continue #Skip things from other modules (including submodules) 
			end
			file, linenum = functionloc(func)
			address = string(linenum)
			args = map(string, func.sig.parameters[2:end])	
			fields = Dict{AbstractString,AbstractString}(
				"module" => mm|>string,
				"kind" => kinds["function"],
				"arity" => string(length(args)),
				"args" => join(args,","),
				"string" => string(name)
				)
			produce(Tag(name,file,address,fields))	
		end
	end
end

function tags(name_sym::Symbol, mm::Module,  value::Union)
	name=string(name_sym)
	Task() do
		filename=module_to_filename(mm) 
			#This is a bad attempt But it is what we got right now
	
		fields=Dict("kind"  => kinds["union"],
					"module"=> string(mm),
					"types"  => join(",",map(string,value.types)),
					"string" => string(value)
					)
		produce(Tag(name,"/name\\s*=/",filename,fields))	
	end
end


function tags(name_sym::Symbol,mm::Module, tt::DataType, record_truename=false)
	name=string(name_sym)
	Task() do
		filename = module_to_filename(mm) 
		#This is a bad attempt But it is what we got right now
		fields=Dict("kind"  => kinds["datatype"],
					"module"=> string(mm),
					"other_type_parameters"=>join(",",map(string,
														  setdiff(tt.parameters,tt.types))),
					"abstract"=> tt.abstract |> string,
					"mutable"=> tt.mutable |> string,
					"size"=> tt.size |> string,
					"supertype"=>supertype(tt) |> string,
					"bitstype"=>isbits(tt) |> string,
					"string" => string(tt)
					)
		if record_truename
			fields["true_name"]=func.name.name |> string
		end
		if tt.name.names |> length >= nfields(tt) #HACK: Avoid Bug where there are not as many names as fields.
			type_fields = ["$fname::"*string(fieldtype(tt,fname)) for fname in fieldnames(tt)]
			fields["fields"] = join(",", type_fields)
		end
		produce(Tag(name,"/^[typealias|type|abstract|immutable]\\s+name\\s*=/",
					filename,fields))
	end	
end

function tags(name_sym::Symbol, mm::Module,  value::Type)
	Task() do 
		for tag in 	tags(name_sym,mm,value.body)
			#TODO: Actually undertand and  special case this fully as a type alias? idk check out `typeof(Vector)`
			tag.fields["kind"] = kinds["type"]
			tag.fields["inner_string"]=tag.fields["string"]
			tag.fields["string"] = string(value)
			produce(tag)
		end
	end
end


function module_to_filename(mm::Module)
	name = mm==Base ? "sysimg" : mm==Core ? "coreimg": string(mm)
	path=Base.find_source_file(name*".jl")
	path!=nothing ? path : "<module $name: unkown path>" 
end

function tags(name_sym::Symbol,mm::Module, submodule::Module)
	name=string(name_sym)
	Task() do 
		filename = module_to_filename(submodule)
		fields=Dict("kind"  => kinds["module"],
					"module"=> module_parent(mm) |> string,
					"string"=> string(submodule)
					)

		produce(Tag(name,"/^module name/",filename,fields))
	end
end


function tags(name_sym::Symbol,mm::Module, variable::Any)
	name=string(name_sym)
	Task() do
		filename=module_to_filename(mm) 
			#This is a bad attempt But it is what we got right now
			#Accessing variables from modules is a bad idea anyway
		fields=Dict("kind"  => kinds["variable"],
					"module"=> string(mm),
					"type"  => string(typeof(variable)),
					"constant" => string(isconst(mm,name_sym)),
					"string" => string(variable)
					)
		produce(Tag(name,"/name\\s*=/",filename,fields))	
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

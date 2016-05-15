#using Optim


kinds = Dict("module"=>"module",
			 "variable"=>"variable",
			 "function"=>"function",
			 "datatype"=>"datatype",
			 "union"=>"union",
			 "type" =>"type"
			 )

immutable Tag
	name::AbstractString
	file::AbstractString
	address::AbstractString
	fields::Dict{AbstractString,AbstractString}
end

function write_header(fp::IO)
	println(fp,"!_TAG_FILE_FORMAT   2   /extended format; --format=1 will not append ;\" to lines/")
	println(fp,"!_TAG_FILE_SORTED   0   /0=unsorted, 1=sorted, 2=foldcase/")
	println(fp,"!_TAG_PROGRAM_AUTHOR    Lyndon White aka Frames aka oxinabox /lyndon.white@reseach.uwa.edu.au")
	println(fp,"!_TAG_PROGRAM_NAME  jltags //")
	#println(fp,"!_TAG_PROGRAM_URL   http://ctags.sourceforge.net    /official site/")
	#println(fp,"!_TAG_PROGRAM_VERSION   5.9~svn20110310 //")
end

"""http://ctags.sourceforge.net/FORMAT
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
		value = escape_string(value)
		print(fp,"\t$field:$value")
	end
	println(fp)
end

###############################



function module_to_filename(mm::Module)
	name = mm==Base ? "sysimg" : mm==Core ? "coreimg": string(mm)
	path = Base.find_source_file(name*".jl")
	path!=nothing ? path : "<module $name: unkown path>" 
end

function docs(func::Function, method::Method)
	try 
		signiture_types = method.sig.types[2:end]
		doc = Base.Docs.doc(func,signiture_types...)
		return doc.meta[:results][1].text[1] #What a long path
	catch ee
		return "No docs found for " * string(method)
	end
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
				"string" => string(func),
				"doc" => docs(value, func),
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
			if name_sym != :Module #HACK/BUG: Module can not have its fieldtype read.
				type_fields = ["$fname::"*string(fieldtype(tt,fname)) for fname in fieldnames(tt)]
				fields["fields"] = join(type_fields,",")
			end
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

function tags(name_sym::Symbol,mm::Module, submodule::Module)
	name=string(name_sym)
	Task() do 

		filename = module_to_filename(submodule)
		fields=Dict("kind"  => kinds["module"],
					"module"=> module_parent(submodule) |> string,
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

###############


function tags_from_module(mm::Module)
	try
		println("++++++++ Loading Tags from  $mm  +++++++")
		Task() do 
			for name_sym in names(mm)
				value = eval(mm,name_sym)
				map(produce, tags(name_sym, mm,  value))
			end
		end |> collect
	catch ee
		warn(string(Module)*" tagging failed. As "* string(ee))
		[]
	end
end

function name2module(name)
	eval(parse("import "*name))
    eval(parse(name))
end

##################################
#Create Module cache
const cache_location = joinpath(Pkg.Dir.path(),"../jltags_cache/")



function get_module_tag_file(module_name)
	cache_name = joinpath(cache_location,module_name*".tags")
	if !isfile(cache_name)
		mkpath(cache_location)
		open(cache_name,"w") do fp
			write_header(fp)
			mod = name2module(module_name)
			for tag in tags_from_module(mod)
				write_tag(fp,tag)
			end
		end
	end	
	cache_name
end



####################################################

function parseall(str)
    #Inspired by https://github.com/JuliaLang/julia/blob/9caa28d50b090cea746ce5c9ad371f5cc2c32644/test/parse.jl#L3
    Task() do 
        pos = start(str)
        while !done(str, pos)
            ex, pos = parse(str, pos)
            produce(ex)
        end
    end
end

function get_modules_names(code)    
    function inner(::Any)
    end
    function inner(ee::Expr)
         if ee.head == :using || ee.head==:importall
            module_name = join(map(string,ee.args),".")
            produce(module_name)
        else
            for arg in ee.args
                inner(arg)
            end
        end
    end
    
    Task() do
        for ee in code |> parseall
            for mod in @task inner(ee)
                produce(mod)
            end
        end
    end
end


######################

for filename in ARGS
	println("Tagging $filename")
		
	code = open(readstring, filename,"r")
	mod_names = append!(["Base", "Core"],collect(get_modules_names(code )))

	open(joinpath(dirname(filename), "."*basename(filename)*".tags"),"w") do fp
		for mod_name in mod_names
			tag_file = get_module_tag_file(mod_name)
			println(fp, open(readstring, tag_file,"r")) #Append it all
		end
	end
end
println("Done")

module MyModule
using Lib
include("another.jl")
include("subdir/yetanother.jl")
using BigLib: thing1, thing2

import Base.show

importall OtherLib

export MyType, foo

type MyType
    x
end

foobuzz = 5
tt=1
export foobuzz, if

macro sayhello()
	return :( println("Hello, world!") )
end

export dead,
	   theparot 

function dead(x)
	2*x
end

function theparot(x)
	dead(x)
end

a,b = 4,3

bar(x) = 2x
foo(a::MyType) = bar(a.x) + 1

show(io, a::MyType) = print(io, "MyType $(a.x)")
end

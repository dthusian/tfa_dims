DOC="""
Expression to Minecraft density function JSON converter

Usage: Run `noise_ast.py` and then enter your expression.

- Targets version 1.21.10 (pack format 88.0)
- Most functions are exactly as they are in the density function documentation.
- Keyword arguments can be specified (e.g. `clamp(input=1, min=2, max=3) => {"type":"minecraft:clamp","input":1,"min":2,"max":3}`)
- Positional arguments can also be used, see below for details
- Use a string literal to call another density function
"""

SINGLE_ARG_FUNCTIONS = [
  "interpolated",
  "flat_cache",
  "cache_2d",
  "cache_once",
  "cache_all_in_cell",
  "abs",
  "half_negative",
  "quarter_negative",
  "squeeze",
  "invert",
  "blend_density"
]

ZERO_ARG_FUNCTIONS = [
  "blend_alpha",
  "blend_offset",
  "beardifier",
  "end_islands"
]

MULTI_ARG_FUNCTIONS = {
  "min": [
    ("argument1", "expr"),
    ("argument2", "expr")
  ],
  "max": [
    ("argument1", "expr"),
    ("argument2", "expr")
  ],
  "old_blended_noise": [
    ("xz_scale", "const"),
    ("y_scale", "const"),
    ("xz_factor", "const"),
    ("y_factor", "const"),
    ("smear_scale_multiplier", "const")
  ],
  "noise": [
    ("noise", "str"),
    ("xz_scale", "const"),
    ("y_scale", "const")
  ],
  "weird_scaled_sampler": [
    ("rarity_value_mapper", "str"),
    ("noise", "str"),
    ("input", "expr")
  ],
  "shifted_noise": [
    ("noise", "str"),
    ("xz_scale", "const"),
    ("y_scale", "const"),
    ("shift_x", "expr"),
    ("shift_y", "expr"),
    ("shift_z", "expr")
  ],
  "range_choice": [
    ("input", "expr"),
    ("min_inclusive", "const"),
    ("max_exclusive", "const"),
    ("when_in_range", "expr"),
    ("when_out_of_range", "expr")
  ],
  "shift_a": [("argument", "str")],
  "shift_b": [("argument", "str")],
  "shift": [("argument", "str")],
  "clamp": [
    ("input", "expr"),
    ("min", "const"),
    ("max", "const")
  ],
  "y_clamped_gradient": [
    ("from_y", "const"),
    ("to_y", "const"),
    ("from_value", "const"),
    ("to_value", "const")
  ],
  "find_top_surface": [
    ("density", "expr"),
    ("upper_bound", "expr"),
    ("lower_bound", "const"),
    ("cell_height", "const")
  ]
}

from ast import *
import json
import sys

def fn_arg12(typ, arg1, arg2):
  return { "type": typ, "argument1": arg1, "argument2": arg2 }

def fn_arg(typ, arg):
  return { "type": typ, "argument": arg }

def parse_arg(coll_args, funcname, arg, argidx, argname, argtype):
  match argtype:
    case "const":
      conv_value = convert(arg)
      if isinstance(conv_value, int) or isinstance(conv_value, float):
        coll_args[argname] = conv_value
      else: raise ValueError(f"In call to function '{funcname}': Argument {argidx} must be a constant")
      
    case "str":
      conv_value = convert(arg)
      if isinstance(conv_value, str):
        coll_args[argname] = conv_value
      else: raise ValueError(f"In call to function '{funcname}': Argument {argidx} must be a string literal")
      
    case "expr":
      coll_args[argname] = convert(arg)

def convert(expr: expr):
  match expr:
    case UnaryOp(op, r):
      match op:
        case UAdd(): return convert(r)
        case USub():
          conv_r = convert(r)
          if isinstance(conv_r, float): return -conv_r
          else: return fn_arg12("minecraft:mul", convert(r), -1)
        case _: raise ValueError(f"in subexpression {unparse(expr)}: unsupported operator {op}")
        
    case BinOp(l, op, r):
      match op:
        case Add(): return fn_arg12("minecraft:add", convert(l), convert(r))
        case Sub(): return fn_arg12("minecraft:add", convert(l), convert(UnaryOp(USub(), r))) # Use the negative constant code
        case Mult(): return fn_arg12("minecraft:mul", convert(l), convert(r))
        
        case Div():
          # Small optimization since Python doesn't natively have a reciprocal operator but MC does
          if l == Constant(1): return fn_arg("minecraft:invert", convert(r))
          else: return fn_arg12("minecraft:mul", convert(l), fn_arg("minecraft:invert", convert(r)))
          
        case Pow():
          match r:
            case Constant(0): return 1.0
            case Constant(1): return convert(l)
            case Constant(2): return fn_arg("minecraft:square", convert(l))
            case Constant(3): return fn_arg("minecraft:cube", convert(l))
            case Constant(v):
              if isinstance(v, int) and v > 0:
                print("warning: Integer power expanded into multiple expr layers", file=sys.stderr)
                lc = convert(l)
                for i in range(v - 1):
                  lc = fn_arg12("minecraft:mul", convert(l), lc)
                return lc
              else: raise ValueError("Non-integer-constant powers not supported")
            case _: raise ValueError("Non-integer-constant powers not supported")
            
        case _: raise ValueError(f"in subexpression {unparse(expr)}: unsupported operator {op}")
        
    case Call(func, args, kws):
      if isinstance(func, Name):
        match func.id:
          case s if s in SINGLE_ARG_FUNCTIONS:
            if len(kws) > 0: raise ValueError(f"Function '{func.id}' does not take keyword arguments")
            if len(args) != 1: raise ValueError(f"Wrong number of arguments for function '{func.id}' (expected 1 found {len(args)})")
            return fn_arg(f"minecraft:{func.id}", convert(args[0]))
          
          case s if s in ZERO_ARG_FUNCTIONS:
            if len(kws) > 0: raise ValueError(f"Function '{func.id}' does not take keyword arguments")
            if len(args) > 0: raise ValueError(f"Function '{func.id}' does not take arguments")
            return { "type": f"minecraft:{func.id}" }
          
          case s if s in MULTI_ARG_FUNCTIONS:
            argdefs = MULTI_ARG_FUNCTIONS[s]
            coll_args = { "type": f"minecraft:{func.id}" }
            if len(args) > len(argdefs): raise ValueError(f"Too many arguments for function '{func.id}'")
            for i, (arg, (argname, argtype)) in enumerate(zip(args, argdefs)):
              parse_arg(coll_args, func.id, arg, f"#{i}", argname, argtype)
            argdefs_dict = dict(argdefs)
            for kwarg in kws:
              if kwarg.arg not in argdefs_dict: raise ValueError(f"Function '{func.id}' does not take argument '{kwarg.arg}'")
              if kwarg.arg in coll_args: raise ValueError(f"In call to function '{func.id}': Argument '{kwarg.arg}' specified more than once")
              parse_arg(coll_args, func.id, kwarg.value, f"'{kwarg.arg}'", kwarg.arg, argdefs_dict[kwarg.arg])
            return coll_args
          
          case _: raise ValueError(f"Unknown function '{func.id}'")
      else: raise ValueError("Invalid function call expression")
      
    case Constant(v):
      match v:
        case int(): return float(v)
        case float(): return v
        case str(): return v
        case _: raise ValueError("Invalid constant")
    case _: raise ValueError("Invalid expression")

if len(sys.argv) > 2 and sys.argv[2] == "--help":
  print(DOC)
else:
  print(json.dumps(convert(parse(input(), mode="eval").body), indent=2))

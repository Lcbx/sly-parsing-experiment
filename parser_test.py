from sly import Lexer, Parser
from io import StringIO
from pprint import pprint

class MyLexer(Lexer):
	tokens = { COMMENT, LINE_END, NAME, FUNC, ARROW, FLOAT, INT, STRING, LONG_STRING }
	ignore = ' '
	literals = { '=', '+', '-', '*', '/', '(', ')', ',', ':' }
	
	# Tokens
	NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'
	NAME['func'] = FUNC
	
	LINE_END = r'\n\t*'
	ARROW = r'->'
	
	FLOAT = r'\d+[.](\d*)?|[.]\d+'
	INT = r'\d+'
	
	@_(r'#.*') # remove '#'
	def COMMENT(self, t): t.value = t.value[1:]; return t
	
	@_(r'".*"') # remove ""
	def STRING(self, t): t.value = t.value[1:-1]; return t
	
	@_(r'"""[\S\s]*"""') # remove """"""
	def LONG_STRING(self, t): t.value = t.value[3:-3]; return t
	
	# Extra action for endlines
	def LINE_END(self, t):
		self.lineno += t.value.count('\n')
		# pass indentation level as value
		t.value = t.value.count('\t')
		return t

	def error(self, t):
		print("Illegal character '%s'" % t.value[0])
		self.index += 1

class MyParser(Parser):
	tokens = MyLexer.tokens
	
	DFLT_TYPE ='Variant'

	def __init__(self):
		self.names = { }
		self.level = 0
		self.parser_level = 0
		self._text = StringIO()
	
	def get_result(self):
		return self._text.getvalue()
	
	def __iadd__(self, txt):
		# automatic indentation
		if '\n' in txt: txt = txt.replace('\n', '\n' + '\t' * self.level)
		self._text.write(txt)
		return self
	
	
	# line -> line LINE_END line
	#      -> stmt
	#      -> COMMENT
	#      -> <empty>
	# stmt -> stmt_impl [COMMENT|<empty>]
	# stmt_impl -> FUNC NAME "(" params ")" -> ret_type
	
	@_('line endline line')
	def line(self, p): pass

	@_('LINE_END')
	def endline(self, p):
		self.parser_level = p.LINE_END
		if self.parser_level >= self.level: self += '\n'
	
	@_('maybe_comment')
	def line(self, p):
		self += p.maybe_comment
	
	@_('')
	def maybe_comment(self, p):
		return ''
	
	@_('COMMENT')
	def maybe_comment(self, p):
		return f'//{p.COMMENT}'
	
	@_('stmt')
	def line(self, p): pass
	
	@_('updateLvl stmt_impl maybe_comment')
	def stmt(self, p):
		if p.maybe_comment: self += ' ' + p.maybe_comment
	
	@_('') # update scope level
	def updateLvl(self, p):
		pLevel = self.parser_level
		while self.level != pLevel:
			if self.level > pLevel: self.level -= 1; self += '\n}\n'
			if self.level < pLevel: self += '{';  self.level += 1; self += '\n';
	
	# a function definition
	@_('FUNC NAME "(" params ")" ret_type')
	def stmt_impl(self, p):
		self += f'{p.ret_type} {p.NAME}(' + ', '.join(map(lambda param : f'{param[0]} {param[1]}',  p.params)) + ')'
	
	@_('param { "," param }')
	def params(self, p):
		return (p.param0 , *p.param1)
	
	@_('')
	def params(self, p):
		return ()
	
	@_('NAME opt_type')
	def param(self, p):
		return p.opt_type or MyParser.DFLT_TYPE, p.NAME
	
	@_('":" NAME')
	def opt_type(self, p):
		return p.NAME
		
	@_('')
	def opt_type(self, p):
		return ''
	
	@_('ARROW NAME')
	def ret_type(self, p):
		return p.NAME
	
	@_('')
	def ret_type(self, p):
		return MyParser.DFLT_TYPE
	
	# yup this is quite long ...
	
	
	@_('INT')
	def stmt_impl(self, p):
		self += f'this is an int : {p.INT}'
		
	@_('FLOAT')
	def stmt_impl(self, p):
		self += f'this is a float : {p.FLOAT}'
	
	@_('STRING')
	def stmt_impl(self, p):
		self += f'this is a string : "{p.STRING}"'
	
	@_('LONG_STRING')
	def stmt(self, p):
		# long strings can be used  as multi-line comments
		self += f'/*{p.LONG_STRING}*/'
	

if __name__ == '__main__':
	lexer = MyLexer()
	parser = MyParser()
	text = """
func test()
# comment1
	# comment2
	func test3( par )
	func test4( par, par ) # comment3
	# comment4
		func test5( par : vec3, par2 :vec2 ) -> float

func test6()

"str"
50
34.1
"""
	pprint([*lexer.tokenize(text)])
	parser.parse(lexer.tokenize(text))
	print('--------------------------')
	print(parser.get_result())

# output :
"""
[Token(type='LINE_END', value=0, lineno=1, index=0, end=1),
 Token(type='FUNC', value='func', lineno=2, index=1, end=5),
 Token(type='NAME', value='test', lineno=2, index=6, end=10),
 Token(type='(', value='(', lineno=2, index=10, end=11),
 Token(type=')', value=')', lineno=2, index=11, end=12),
 Token(type='LINE_END', value=0, lineno=2, index=12, end=13),
 Token(type='COMMENT', value=' comment1', lineno=3, index=13, end=23),
 Token(type='LINE_END', value=1, lineno=3, index=23, end=25),
 Token(type='COMMENT', value=' comment2', lineno=4, index=25, end=35),
 Token(type='LINE_END', value=1, lineno=4, index=35, end=37),
 Token(type='FUNC', value='func', lineno=5, index=37, end=41),
 Token(type='NAME', value='test3', lineno=5, index=42, end=47),
 Token(type='(', value='(', lineno=5, index=47, end=48),
 Token(type='NAME', value='par', lineno=5, index=49, end=52),
 Token(type=')', value=')', lineno=5, index=53, end=54),
 Token(type='LINE_END', value=1, lineno=5, index=54, end=56),
 Token(type='FUNC', value='func', lineno=6, index=56, end=60),
 Token(type='NAME', value='test4', lineno=6, index=61, end=66),
 Token(type='(', value='(', lineno=6, index=66, end=67),
 Token(type='NAME', value='par', lineno=6, index=68, end=71),
 Token(type=',', value=',', lineno=6, index=71, end=72),
 Token(type='NAME', value='par', lineno=6, index=73, end=76),
 Token(type=')', value=')', lineno=6, index=77, end=78),
 Token(type='COMMENT', value=' comment3', lineno=6, index=79, end=89),
 Token(type='LINE_END', value=1, lineno=6, index=89, end=91),
 Token(type='COMMENT', value=' comment4', lineno=7, index=91, end=101),
 Token(type='LINE_END', value=2, lineno=7, index=101, end=104),
 Token(type='FUNC', value='func', lineno=8, index=104, end=108),
 Token(type='NAME', value='test5', lineno=8, index=109, end=114),
 Token(type='(', value='(', lineno=8, index=114, end=115),
 Token(type='NAME', value='par', lineno=8, index=116, end=119),
 Token(type=':', value=':', lineno=8, index=120, end=121),
 Token(type='NAME', value='vec3', lineno=8, index=122, end=126),
 Token(type=',', value=',', lineno=8, index=126, end=127),
 Token(type='NAME', value='par2', lineno=8, index=128, end=132),
 Token(type=':', value=':', lineno=8, index=133, end=134),
 Token(type='NAME', value='vec2', lineno=8, index=134, end=138),
 Token(type=')', value=')', lineno=8, index=139, end=140),
 Token(type='ARROW', value='->', lineno=8, index=141, end=143),
 Token(type='NAME', value='float', lineno=8, index=144, end=149),
 Token(type='LINE_END', value=0, lineno=8, index=149, end=150),
 Token(type='LINE_END', value=0, lineno=9, index=150, end=151),
 Token(type='FUNC', value='func', lineno=10, index=151, end=155),
 Token(type='NAME', value='test6', lineno=10, index=156, end=161),
 Token(type='(', value='(', lineno=10, index=161, end=162),
 Token(type=')', value=')', lineno=10, index=162, end=163),
 Token(type='LINE_END', value=0, lineno=10, index=163, end=164),
 Token(type='LINE_END', value=0, lineno=11, index=164, end=165),
 Token(type='STRING', value='str', lineno=12, index=165, end=170),
 Token(type='LINE_END', value=0, lineno=12, index=170, end=171),
 Token(type='INT', value='50', lineno=13, index=171, end=173),
 Token(type='LINE_END', value=0, lineno=13, index=173, end=174),
 Token(type='FLOAT', value='34.1', lineno=14, index=174, end=178),
 Token(type='LINE_END', value=0, lineno=14, index=178, end=179)]
--------------------------

Variant test()
// comment1
// comment2
{
	Variant test3(Variant par)
	Variant test4(Variant par, Variant par) // comment3
	// comment4
	{
		float test5(vec3 par, vec2 par2)
	}

}
Variant test6()

this is a string : "str"
this is an int : 50
this is a float : 34.1

"""

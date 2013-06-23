out: parser.py
	./parser.py 2> error 1> out

clean:
	rm parser.out error out
	rm *.pyc
	rm parsetab*

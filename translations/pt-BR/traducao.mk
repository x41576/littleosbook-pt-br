# Compila a versão em português (pt-BR). Incluído pelo Makefile da raiz, do qual
# reaproveita CHAPTERS, CSS, BIB, CITATION e TEX_HEADER (uma única lista de
# capítulos para o livro e para a tradução).
#
#   make pt-BR        gera build/pt-BR/book.html
#   make pt-BR-pdf    gera build/pt-BR/book.pdf (precisa de pdflatex)
#
# Capítulos ainda não traduzidos entram em inglês (fallback por arquivo), então o
# livro compila a qualquer momento.
#
# Requer pandoc >= 2.11 (o Makefile original usa opções do pandoc 1.x que não
# existem mais: -S, --latex-engine, --chapters).

PT_DIR      = translations/pt-BR
PT_CAP      = $(PT_DIR)/capitulos
PT_OUT      = build/pt-BR
PT_TEMPLATE = $(PT_DIR)/template.html
PT_TEX_HEADER = $(PT_DIR)/header.tex

PT_CHAPTERS = $(foreach f,$(CHAPTERS),$(if $(wildcard $(PT_CAP)/$(f)),$(PT_CAP)/$(f),$(f)))

PT_COMMON = -f markdown+smart --citeproc --bibliography $(BIB) --csl $(CITATION) \
            -V lang=pt-BR

.PHONY: pt-BR pt-BR-pdf pt-BR-clean

pt-BR: $(PT_OUT)/book.html

pt-BR-pdf: $(PT_OUT)/book.pdf

$(PT_OUT)/book.html: $(PT_CHAPTERS) $(CSS) $(PT_TEMPLATE) $(BIB) $(CITATION) $(wildcard images/*.png)
	@command -v pandoc >/dev/null || { echo "pandoc não encontrado (precisa >= 2.11): brew install pandoc"; exit 1; }
	mkdir -p $(PT_OUT)/images $(PT_OUT)/files
	pandoc -s $(PT_COMMON) --toc --number-sections -c $(CSS) \
	       --template $(PT_TEMPLATE) $(PT_CHAPTERS) -o $@
	cp $(CSS) $(PT_OUT)/
	cp images/*.png $(PT_OUT)/images/
	cp files/* $(PT_OUT)/files/

$(PT_OUT)/book.pdf: $(PT_CHAPTERS) $(PT_TEX_HEADER) $(BIB) $(CITATION)
	@command -v pandoc >/dev/null || { echo "pandoc não encontrado (precisa >= 2.11): brew install pandoc"; exit 1; }
	mkdir -p $(PT_OUT)
	pandoc $(PT_COMMON) --toc -H $(PT_TEX_HEADER) --pdf-engine=pdflatex \
	       --top-level-division=chapter $(PT_CHAPTERS) -o $@

pt-BR-clean:
	rm -rf $(PT_OUT)

#!/usr/bin/env python
"""
Script based on Fernando Perez's latex2rst.py using the BSD license
https://github.com/fperez/lacquer/blob/master/lacquer/latex2rst

Convert a latex document to rst.

Usage:

  latex2rst filename.tex > filename.rst

or equivalently

  latex2rst -s filename.tex

You may still need to edit the rst file by hand to fix little things, but most
of the equations should be correctly converted.

"""

from textwrap import fill
import os
import re
from optparse import OptionParser

supplement = {"footnote": [], }
def repl1(obj):
    eq = obj.group(1)
    eq = eq.replace("\n", " ")
    eq = fill(eq, 100000)
    return "\n.. math::\n\n    %s\n" % eq
def item(obj):
    l = obj.group(1)
    l = l.replace("\item", "* ")
    return l
def footnote(obj):
    note = obj.group(1)
    note.replace('\n', ' ')
    supplement["footnote"] += ['.. [#] ' + note]
    return '[#]_'
def enum(obj):
    en = obj.group(1)
    en = en.replace("\item", "#. ")
    return en
def verbatim(obj):
    return "::\n\n{0}".format(obj.group(1))
def repl6(obj):
    eq = obj.group(1)
    eq = eq.replace("\n", " ")
    eq = fill(eq, 100000)
    return "\n.. math::\n    :nowrap:\n\n    %s\n" % eq
def repl4(obj):
    # in general, there can be some equation (group 1), then the label (group
    # 2) and then some more equation text (group 3), so we need to join the
    # equation text and put the label in front:
    eq = obj.group(1)
    label = obj.group(2)
    eq += " " + obj.group(3)
    eq = eq.replace("\n", " ")
    eq = fill(eq, 100000)
    return "\n.. math::\n    :label: %s\n\n    %s\n" % (label, eq)

def repl_chapter(obj):
    title = obj.group(1)
    return "{1}\n{0}\n{1}\n".format(title, "-"*len(title))
def repl_section(obj):
    title = obj.group(1)
    return "{0}\n{1}\n".format(title, "="*len(title))
def repl_subsection(obj):
    title = obj.group(1)
    return "{0}\n{1}\n".format(title, "*"*len(title))
def repl_subsubsection(obj):
    title = obj.group(1)
    return "{0}\n{1}\n".format(title, "-"*len(title))
def repl_minisec(obj):
    title = obj.group(1)
    return "{0}\n{1}\n".format(title, "~"*len(title))

def main():
    parser = OptionParser(usage="[options] args")
    parser.add_option("-s", "--save", dest="save", action="store_true",
            default=False, help="Save the output to a .rst file")
    options, args = parser.parse_args()
    if len(args) != 1:
        parser.print_help()
        return

    # those substitutions will be caried in the order as specified in the list:
    simple_substitutions = [
            # general substitutions:
            {
                r" +\n": r"\n",
            },
            {
                r"([a-zA-Z0-9,;:\)])\n([a-zA-Z0-9\*])": r"\1 \2",
            },
            {
                r"\\textit{(.*?)}": r"*\1*",
                r"\\textbf{(.*?)}": r"**\1**",
                r"\\texttt{(.*?)}": r"``\1``",
                r"\\url{(.*?)}": r"\1",
                r"\A%": r".. ",
                r"\n%": r"\n.. ",
                r"(\\label{.*?):(.*?})": r"\1_\2",
            },
            {
                r"\\label{(.*?)}": r"`\1`:",
            },

            # custom substitutions (you might add your own here):
            {
                r"\\def\\be\{.*\}": r"",
                r"\\def\\ee\{.*\}": r"",
            },
            {
                #r"(?<!\\def)\\be(?=[^\w])": r"\\begin{equation}",
                #r"(?<!\\def)\\ee(?=[^\w])": r"\\end{equation}",
                #r"(?<!\\def)\\ba(?=[^\w])": r"\\begin{array}",
                #r"(?<!\\def)\\ea(?=[^\w])": r"\\end{array}",
                #r"(?ms)\\left\((\\mat{.+?})\\right\)": r"\1",
                #r"\(\\ref{(.+?)}\)": r":eq:`\1`",
                r"\\qg":r"|qg|",
                r"\\nix{(.*?)}":r"|nix| \1",
                r"\\win{(.*?)}":r"|win| \1",
                r"\\osx{(.*?)}":r"|osx| \1",
                r"(\\cite{(.*?)})":r"[\2]_",
                r"\\index{(.*?)}":r":index:`\1`",
                r"\\keyboard{(.*?)}":r":kbd:`\1`",
                r"\\dialog{(.*?)}":r":guilabel:`\1`",
                r"\\toolbtntwo{(.*?)}{(.*?)}":r"|\1| :guilabel:`\2`",
            },
        ]
    filename = args[0]
    s = open(filename).read()
    # apply the simple substitutions
    for stage in simple_substitutions:
        for pattern in stage:
            s = re.sub(pattern, stage[pattern], s)

    # convert equations:
    s = re.sub("(?ms)\$\$(.+?)\$\$", repl1, s)
    s = re.sub(r"(?ms)\\begin{equation\*}(.+?)\\end{equation\*}", repl1, s)
    s = re.sub(r"(?ms)(\\begin{eqnarray\*}.+?\\end{eqnarray\*})", repl6, s)
    s = re.sub(r"(?ms)\\begin{equation}(.*?)\\label{(.+?)}(.+?)\\end{equation}",
            repl4, s)
    s = re.sub(r"(?ms)(\\begin{enumerate}.+?\\end{enumerate})", enum, s)
    s = re.sub(r"(?ms)(\\begin{itemize}.+?\\end{itemize})", item, s)
    s = re.sub(r"(?ms)\\begin{verbatim}(.+?)\\end{verbatim}", verbatim, s)
    s = re.sub(r"(\\begin{itemize})", "\n", s)
    s = re.sub(r"(\\end{itemize})", "\n", s)
    s = re.sub(r"(\\begin{enumerate})", "\n", s)
    s = re.sub(r"(\\end{enumerate})", "\n", s)
    s = re.sub(r"(?ms)\\footnote{(.*?)}", footnote, s)
    s = re.sub(r"(?ms)\\begin{verbatim}(.+?)\\end{verbatim}", verbatim, s)
    # convert titles:
    s = re.sub(r"\\chapter{(.+?)}", repl_chapter, s)
    s = re.sub(r"\\section\*?{(.+?)}", repl_section, s)
    s = re.sub(r"\\subsection\*?{(.+?)}", repl_subsection, s)
    s = re.sub(r"\\subsubsection\*?{(.+?)}", repl_subsubsection, s)
    s = re.sub(r"\\minisec\*?{(.+?)}", repl_minisec, s)

    # add supplement:
    s += '\n\n'.join(['\n '.join(supplement[i]) for i in supplement.keys()])
    # either save to a file or dump to stdout:
    if options.save:
        outfile = os.path.splitext(filename)[0] + ".rst"
        open(outfile, "w").write(s)
    else:
        print s

if __name__ == '__main__':
    main()

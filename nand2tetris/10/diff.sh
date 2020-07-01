#!/usr/bin/env bash

# we use `tidy` in this script, so we benefit from two facts:
#   1. file format problem, the referenced file is dos,
#        while ours is unix(though, --strip-trailing-cr is worth a try)
#   2. indent problem, we dont handle indent in out xml output,
#        but the referenced file has indent indeed.
#
# However, use the provided tools/TextComparer.sh can also solve the two problem
# above, I am just used to unix `diff` command.
# What's more, I observed that tools/TextComparer.sh is much more slower that `diff`.

set -e
cmp_dir='cmp'

if [[ -n "$1" ]]; then
    jack_files="$1"
else
    jack_files=`fd --extension jack`
fi

# mkdir if not exist
mkdir -p $cmp_dir

for jack_file in $jack_files; do
    echo "checking ${jack_file}..."
    base=`echo $jack_file | cut -d'.' -f 1`
    token_file="${base}T.xml"
    my_token_file=`echo -n $token_file | tr '/' '_'`
    my_token_file="${cmp_dir}/${my_token_file}"
    ./Jack2VM.py --print-token-as-xml $jack_file > $my_token_file

    my_token_file_after_tidy="${my_token_file}.tidy"
    tidy -xml -i -q $my_token_file > $my_token_file_after_tidy

    ref_token_file="${base}T.xml"
    ref_token_file_after_tidy=`echo -n ${ref_token_file}.ref.tidy | tr '/' '_'`
    ref_token_file_after_tidy="${cmp_dir}/${ref_token_file_after_tidy}"
    tidy -xml -i -q $ref_token_file > $ref_token_file_after_tidy

    echo -e "\tchecking token"
    diff $my_token_file_after_tidy $ref_token_file_after_tidy


    ast_file="${base}.xml"
    my_ast_file=`echo -n $ast_file | tr '/' '_'`
    my_ast_file="${cmp_dir}/${my_ast_file}"
    ./Jack2VM.py --print-ast-as-xml $jack_file > $my_ast_file

    my_ast_file_after_tidy="${my_ast_file}.tidy"
    tidy -xml -i -q $my_ast_file > $my_ast_file_after_tidy

    ref_ast_file="${base}.xml"
    ref_ast_file_after_tidy=`echo -n ${ref_ast_file}.ref.tidy | tr '/' '_'`
    ref_ast_file_after_tidy="${cmp_dir}/${ref_ast_file_after_tidy}"
    tidy -xml -i -q $ref_ast_file > $ref_ast_file_after_tidy

    echo -e "\tchecking ast"
    diff $my_ast_file_after_tidy $ref_ast_file_after_tidy

    echo ""
done

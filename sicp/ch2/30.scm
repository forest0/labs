(define (square-tree-v1 tree)
  (cond ((null? tree) tree)
        ((pair? tree)
         (cons
           (square-tree-v1 (car tree))
           (square-tree-v1 (cdr tree))))
        (else
          (square tree))))

(define (square-tree-v2 tree)
  (map
    (lambda (sub-tree)
      (cond ((null? sub-tree) sub-tree)
            ((pair? sub-tree) (square-tree-v2 sub-tree))
            (else
              (square sub-tree))))
    tree))

(define (tree-map f tree)
  (cond ((null? tree) tree)
        ((pair? tree)
         (cons
           (tree-map f (car tree))
           (tree-map f (cdr tree))))
        (else
          (f tree))))

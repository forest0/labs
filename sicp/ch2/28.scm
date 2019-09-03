(define (fringe tree)
  (cond ((null? tree) tree)
        ((list? tree)
         (append
           (fringe (car tree))
           (fringe (cdr tree))))
        (else
          (list tree))))

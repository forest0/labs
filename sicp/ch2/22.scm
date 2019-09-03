(define (my-for-each f items)
  (if (null? items)
      #t
      (begin
        (f (car items))
        (my-for-each f (cdr items)))))

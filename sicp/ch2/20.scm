(define (same-parity x . l)
  (filter
    (if (even? x) even? odd?)
    (cons x l)))

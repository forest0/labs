(define (my-reverse l)
  (define (iter lt result)
    (if (null? lt)
        result
        (iter (cdr lt) (cons (car lt) result))))
  (iter l '()))

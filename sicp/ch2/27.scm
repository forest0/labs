(define (deep-reverse l)
  (define (iter lt result)
    (cond ((null? lt) result)
          ((list? (car lt))
           (iter
             (cdr lt)
             (cons (deep-reverse (car lt)) result)))
          (else
            (iter
              (cdr lt)
              (cons (car lt) result)))))
  (iter l '()))

(define (subsets s)
  (if (null? s)
      (list '())
      (let ((rest (subsets (cdr s)))
            (one (car s)))
        (append
          rest
          (map
            (lambda (set)
              (append (list one) set))
            rest)))))

(define (symbol-equal? a b)
  (eq? a b))

(define (list-equal? a b)
  (cond ((and (null? a) (null? b))
         #t)
        ((or (null? a) (null? b))
         #f)
        ((my-equal? (car a) (car b))
         (my-equal? (cdr a) (cdr b)))
        (else
          #f)))

(define (my-equal? a b)
  (cond ((and (symbol? a) (symbol? b))
         (symbol-equal? a b))
        ((and (list? a) (list? b))
         (list-equal? a b))
        (else
          (error "Wrong type input a and b -- equal?" a b))))

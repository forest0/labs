(define (square-list-v1 items)
  (if (null? items)
      '()
      (cons
        (square (car items))
        (square-list-v1 (cdr items)))))

(define (square-list-v2 items)
  (map square items))

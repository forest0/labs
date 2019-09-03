(define (accumulate op initial sequence)
  (if (null? sequence)
      initial
      (op
        (car sequence)
        (accumulate op initial (cdr sequence)))))

(define (map p sequence)
  (accumulate
    (lambda (x y)
      (cons
        (p x)
        y))
    '()
    sequence))

; (define (count-leaves tree)
;   (cond ((null? tree) 0)
;         ((pair? tree)
;          (+
;            (count-leaves (car tree))
;            (count-leaves (cdr tree))))
;         (else 1)))

(define (count-leaves tree)
  (accumulate
    +
    0
    (map
      (lambda (sub-tree)
        (if (pair? sub-tree)
            (count-leaves sub-tree)
            1))
      tree)))

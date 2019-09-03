(load "66.scm")

(define (triples s t u)
  (cons-stream
    (list (stream-car s) (stream-car t) (stream-car u)) ; i, j, k
    (cons-stream
      (list (stream-car s) (stream-car t) (stream-car (stream-cdr u))) ; i, j, k+1
      (interleave
        (stream-map (lambda (pair) (cons (stream-car s) pair)) ; i, j+1..., k+1...
                    (pairs (stream-cdr t) (stream-cdr u))) ; j+1..., k+1...
        (triples (stream-cdr s) (stream-cdr t) (stream-cdr u)))))) ; i+1..., j+1..., k+1...

; out of memory when try to output 10 items...
(define pythagorean-stream
  (stream-filter (lambda (triple)
                   (= (+ (square (car triple))
                         (square (cadr triple)))
                      (square (caddr triple))))
                 (triples integers integers integers)))

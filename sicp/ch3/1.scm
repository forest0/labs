(define (make-accumulator value)
  (lambda (num)
    (set! value (+ value num))
    value))

(define (make-point x y)
  (cons x y))

(define (x-point p)
  (car p))

(define (y-point p)
  (cdr p))

(define (print-point p)
  (newline)
  (display "(")
  (display (x-point p))
  (display ",")
  (display (y-point p))
  (display ")"))
  (newline)

(define (make-segment start-point end-point)
  (cons start-point end-point))

(define (start-segment seg)
  (car seg))

(define (end-segment seg)
  (cdr seg))

(define (midpoint-segment seg)
  (define (average a b)
    (/ (+ a b) 2))
  (let ((s (start-segment seg))
        (e (end-segment seg)))
    (make-point
      (average (x-point s) (x-point e))
      (average (y-point s) (y-point e)))))


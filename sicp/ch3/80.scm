(define (scale-stream stream scale)
  (stream-map (lambda (x) (* scale x))
              stream))

(define (add-stream . args)
  (apply stream-map + args))

(define (integral delayed-integrand initial-value dt)
  (define int
    (cons-stream
      initial-value
      (let ((integrand (force delayed-integrand)))
        (add-stream (scale-stream integrand dt) int))))
  int)

(define (RLC R L C dt)
  (lambda (vC0 iL0)
    ; this two lines must come first
    (define iL (integral (delay diL) iL0 dt))
    (define vC (integral (delay dvC) vC0 dt))
    (define vC*1/L (scale-stream vC (/ 1 L)))
    (define -iL*R/L (scale-stream iL (- (/ R L))))
    (define diL (add-stream vC*1/L -iL*R/L))
    (define dvC (scale-stream iL (/ -1 C)))
    (stream-map list vC iL)))

(define RLC1
  ((RLC 1 1 0.2 0.1) 10 0))

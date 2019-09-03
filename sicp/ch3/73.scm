(define (add-stream . args)
  (apply stream-map + args))

(define (scale-stream stream scale)
  (stream-map (lambda (x) (* scale x))
              stream))

(define (integral integrand initial-value dt)
  (define int
    (cons-stream initial-value
                 (add-stream int
                             (scale-stream integrand dt))))
  int)

(define (RC R C dt)
  (lambda (i v0)
    (let ((Ri (scale-stream i R))
          (i/C (scale-stream i (/ 1 C))))
      (add-stream Ri
                  (integral i/C v0 dt)))))

(define RC1 (RC 5 1 0.5))

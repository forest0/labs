(define (add-stream . streams)
  (apply stream-map + streams))

(define (mul-stream . streams)
  (apply stream-map * streams))

(define (div-stream . streams)
  (apply stream-map / streams))

(define (scale-stream stream scale)
  (stream-map (lambda (x) (* scale x))
              stream))

(define ones (cons-stream 1 ones))

(define integers
  (cons-stream 1
               (add-stream
                 ones
                 integers)))

(define (show-to stream n)
  (if (> n 0)
      (begin (newline)
             (display (stream-car stream))
             (show-to (stream-cdr stream)
                      (- n 1)))))

(define harmonic-series
  (div-stream ones integers))

(define (integrate-series a)
  (mul-stream harmonic-series a))

(define exp-series
  (cons-stream 1
               (integrate-series exp-series)))

(define cosine-series
  (cons-stream 1
               (integrate-series
                 (scale-stream sine-series -1))))

(define sine-series
  (cons-stream 0
               (integrate-series cosine-series)))

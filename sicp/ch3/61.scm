(load "60.scm")

; (define (invert-unit-series s)
;   (cons-stream 1
;                (scale-stream
;                  (mul-series (invert-unit-series s)
;                              (stream-cdr s))
;                  -1)))

(define (invert-unit-series s)
  (define invert
    (cons-stream 1
                 (scale-stream
                   (mul-series invert
                               (stream-cdr s))
                   -1)))
  invert)

(define (add-stream . streams)
  (apply stream-map + streams))

(define (partial-sum s)
  (cons-stream (stream-car s)
               (add-stream (partial-sum s)
                           (stream-cdr s))))

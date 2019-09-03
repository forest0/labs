(define (add-stream . streams)
  (apply stream-map + streams))

(define (mul-stream . streams)
  (apply stream-map * streams))

(define ones (cons-stream 1 ones))

(define integers (cons-stream 1
                             (add-stream integers ones)))

(define factorials
  (cons-stream 1 (mul-streams factorials (stream-cdr integers))))

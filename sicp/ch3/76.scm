(define (adjacent-paris s)
  (stream-map list s (stream-cdr s)))

(define (smooth input-stream)
  (stream-map (lambda (p) (/ (+ (car p) (cadr p)) 2))
              (adjacent-pair input-streamo)))

(define smoothed-sense-data (smooth input-stream))

(define zero-crossings
  (strem-map sign-change-detector
             smoothed-sense-data
             (cons-stream 0 smoothed-sense-data)))

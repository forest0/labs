(define (monte-carlo experiment-stream passed failed)
  (define (next passed failed)
    (cons-stream
      (/ passed (+ passed failed))
      (monte-carlo
        (stream-cdr experiment-stream) passed failed)))
  (if (stream-car experiment-stream)
      (next (+ passed 1) failed)
      (next passed (+ failed 1))))

(define ones (cons-stream 1 ones))

(define (random-in-range low high)
  (let ((range (- high low)))
    (+ low (random range))))

(define (random-points-in-zone x1 x2 y1 y2)
  (stream-map (lambda (x)
                (cons (random-in-range x1 x2)
                      (random-in-range y1 y2)))
              ones))

(define (estimate-integral x1 x2 y1 y2 P)
  (define experiment-stream
    (stream-map (lambda (point) (P point))
                (random-points-in-zone x1 x2 y1 y2)))
  (let ((zone-area (* (- x2 x1)
                      (- y2 y1))))
    (stream-map (lambda (prob) (* zone-area prob))
                (monte-carlo experiment-stream 0 0))))

(define pi-stream
  (estimate-integral 0.0 2.0 0.0 2.0
                     (lambda (point)
                       (let ((x (car point))
                             (y (cdr point)))
                         (< (+ (square (- x 1.0))
                               (square (- y 1.0)))
                            1.0)))))

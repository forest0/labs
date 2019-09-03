(define (random-numbers request-stream)
  (define rand-init 0)
  (define (rand-update x) (+ x 1)) ; just for demonstration
  (define (handle-request n req)
    (cond ((eq? req 'generate)
           (rand-update n))
          ((eq? req 'reset)
           rand-init)
          (else error "unknown operation")))
  (define randoms
    (cons-stream
      rand-init
      (stream-map handle-request randoms request-stream)))
  randoms)

(define gen-all-the-way (cons-stream 'generate gen-all-the-way))
(define random-all-the-way (random-numbers gen-all-the-way))

(define (add-stream . args)
  (apply stream-map + args))
(define ones (cons-stream 1 ones))
(define integers (cons-stream 1
                              (add-stream integers ones)))
(define regenerate-every-7-request
  (stream-map (lambda (n)
                (if (= (remainder n 7) 0)
                    'reset
                    'generate))
              integers))
(define regenerate-every-7
  (random-numbers regenerate-every-7-request))

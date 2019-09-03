(define (enumerate-interval start end)
  (define (iter cur result)
    (if (> cur end)
        result
        (iter
          (+ cur 1)
          (append
            result
            (list cur)))))
  (iter start '()))

(define (accumulate op initial sequence)
  (if (null? sequence)
      initial
      (op
        (car sequence)
        (accumulate op initial (cdr sequence)))))

(define (flatmap f sequence)
  (accumulate
    append
    '()
    (map
      f
      sequence)))

(define (unique-triples n)
  (flatmap
    (lambda (i)
      (flatmap
        (lambda (j)
          (map
            (lambda (k) (list i j k))
            (enumerate-interval 1 (- j 1))))
        (enumerate-interval 1 (- i 1))))
    (enumerate-interval 1 n)))

(define (sum-triples n s)
  (define (sum t)
    (accumulate + 0 t))
  (filter
    (lambda (t)
      (= s (sum t)))
    (unique-triples n)))

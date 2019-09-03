(define (f-recursive n)
  (if (< n 3) n
      (+ (f-recursive (- n 1))
         (* 2 (f-recursive (- n 2)))
         (f-recursive (- n 3)))))

(define (f n)
  (define (f-iter a b c count)
    (if (= count 0) a
        (f-iter (+ a (* 2 b) c) a b (- count 1))))
  (if (< n 3) n
      (f-iter 2 1 0 (- n 2))))

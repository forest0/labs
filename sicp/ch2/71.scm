(load "69.scm")

(define (pow base exp)
  (define (iter b e result)
    (cond ((= e 0) result)
          ((even? e) (iter (* b b) (/ e 2) result))
          (else (iter b (- e 1) (* b result)))))
  (iter base exp 1))

(define (generate-pairs n)
  (define (iter cur result)
    (if (= cur n)
        result
        (iter (+ cur 1)
              (cons (list cur (pow 2 cur))
                    result))))
  (iter 0 '()))

(generate-huffman-tree (generate-pairs 5))

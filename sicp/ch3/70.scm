(load "54.scm")

(define (merge-weighted s1 s2 weight)
  (cond ((stream-null? s1) s2)
        ((stream-null? s2) s1)
        (else
          (let ((w1 (weight (stream-car s1)))
                (w2 (weight (stream-car s2))))
            (if (<= w1 w2) ; same wight does not necessarily mean same pair
                (cons-stream (stream-car s1)
                             (merge-weighted (stream-cdr s1) s2 weight))
                (cons-stream (stream-car s2)
                             (merge-weighted s1 (stream-cdr s2) weight)))))))

(define (weighted-pairs s1 s2 weight)
  (cons-stream
    (list (stream-car s1) (stream-car s2))
    (merge-weighted
      (stream-map (lambda (x) (list (stream-car s1) x))
                  (stream-cdr s2))
      (weighted-pairs (stream-cdr s1) (stream-cdr s2) weight)
      weight)))

(define ordered-pairs-a
  (weighted-pairs integers
                  integers
                  (lambda (p) (+ (car p) (cadr p)))))

(define (divisible-by-any n divs)
  (cond ((null? divs) #f)
        ((= 0 (remainder n (car divs))) #t)
        (else (divisible-by-any n (cdr divs)))))

(define integers-not-divisible-by-2-3-5
  (stream-filter (lambda (x) (not (divisible-by-any x (list 2 3 5))))
                 integers))

(define ordered-pairs-b
  (weighted-pairs integers-not-divisible-by-2-3-5
                  integers-not-divisible-by-2-3-5
                  (lambda (p) (let ((i (car p))
                                    (j (cadr p)))
                                (+ (* 2 i)
                                   (* 3 j)
                                   (* 5 i j))))))

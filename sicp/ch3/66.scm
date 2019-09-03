(load "54.scm")

(define (interleave s1 s2) (if (stream-null? s1)
      s2
      (cons-stream (stream-car s1)
                   (interleave s2 (stream-cdr s1)))))

(define (pairs s t)
  (cons-stream
    (list (stream-car s) (stream-car t))
    (interleave
      (stream-map (lambda (x) (list (stream-car s) x))
                  (stream-cdr t))
      (pairs (stream-cdr s)
             (stream-cdr t)))))

(define (show-to stream n)
  (define (iter stream i)
    (if (<= i n)
        (begin (newline)
               (display i)
               (display ": ")
               (display (stream-car stream))
               (iter (stream-cdr stream) (+ i 1)))))
  (iter stream 1))

; (show-to (pairs integers integers) 40)

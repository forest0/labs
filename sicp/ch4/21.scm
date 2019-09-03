((lambda (n)

   ((lambda (func)
     (func func n))
    (lambda (fib k)
      (if (< k 2)
          k
          (+ (fib fib (- k 1))
             (fib fib (- k 2)))))))

 6)

(define (f x)
  ((lambda (my-even? my-odd?)
     (my-even? my-even? my-odd? x))

   (lambda (ev? od? n)
     (if (= n 0)
         true
         (od? ev? od? (- n 1))))

   (lambda (ev? od? n)
     (if (= n 0)
         false
         (ev? ev? od? (- n 1))))))

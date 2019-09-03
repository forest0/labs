(load "test-util.scm")

(define (run-tests eval env)

  (define (make-test-interface)
    (define (test testcase)
      (equal? (eval (input testcase) env)
           (cadr testcase)))
    (define (input testcase)
      (car testcase))
    (define (expect testcase)
      (cadr testcase))
    (define (got testcase)
      (eval (input testcase) env))

    (define (dispatch m)
      (cond ((eq? m 'test) test)
            ((eq? m 'input) input)
            ((eq? m 'expect) expect)
            ((eq? m 'got) got)
            (else (error "Unknown operation for test interface --" m))))
    dispatch)

  (let ((testsets (make-test (make-test-interface))))

    ((testsets 'add) "primitive"
                    (list
                      (list 1 1)
                      (list "a" "a")))

    ((testsets 'add) "quote"
                    (list
                      (list (list 'quote 'a) 'a)
                    ))

    ((testsets 'add) "and"
                    (list
                      (list '(and) true)
                      (list '(and false) false)
                      (list '(and 1) 1)
                      (list '(and 1 2) 2)
                      (list '(and false 2) false)
                      (list '(and 1 false) false)
                      (list '(and false false) false)
                      (list '(and 1 2 3) 3)
                      (list '(and 1 2 false) false)
                      ))

    ((testsets 'add) "or"
                    (list
                      (list '(or) false)
                      (list '(or 1) 1)
                      (list '(or 1 2) 1)
                      (list '(or false 2) 2)
                      (list '(or 1 false) 1)
                      (list '(or false false) false)
                      (list '(or 1 2 3) 1)
                      ))

    ((testsets 'add) "if"
                    (list
                      (list '(if true 1) 1)
                      (list '(if true 1 0) 1)
                      (list '(if false 1 0) 0)
                      (list '(if false 1) false)
                      (list '(if (< 0 1) 1 0) 1)
                      (list '(if (> 0 1) 1 0) 0)
                      (list '(if (> 0 1) 1) false)
                      (list '(if (and true true) 1 2) 1)
                      (list '(if (and true false) 1 2) 2)
                      (list '(if (and true true)
                                 (and 1 2)
                                 3)
                            2)
                      (list '(if (and true false)
                                 (and 2 3)
                                 3)
                            3)
                      ))

    ((testsets 'add) "begin"
                    (list
                      (list '(begin) false)
                      (list '(begin 1) 1)
                      (list '(begin 1 2) 2)
                      (list '(begin (+ 1 2)) 3)
                      (list '(begin (and 1 2) (or 3 4)) 3)
                      (list '(begin (+ 1 3) (* 2 4)) 8)
                      ; todo
                      (list '(begin
                               (define a 1)
                               (define b 2)
                               (+ a b))
                            3)
                      ))

    ((testsets 'add) "cond"
                    (list
                      (list '(cond (true 1)) 1)
                      (list '(cond (false 1)) false)
                      (list '(cond (false 0) (true 1)) 1)
                      (list '(cond (false 0) (else 1)) 1)
                      (list '(cond ((> 0 1) 0)) false)
                      (list '(cond ((< 0 1) 1) (else 0)) 1)
                      (list '(cond ((> 0 1) 1) (else 0)) 0)
                      (list '(cond (true 1) (else 2)) 1)
                      (list '(cond (false 1) (else 2)) 2)
                      (list '(cond ((or true false) 1)
                                   (else 2))
                            1)
                      (list '(cond ((and true false) 1)
                                   (else 2))
                            2)
                      (list '(cond (true (or 1 2))
                                   (else (or 3 4)))
                            1)
                      (list '(cond (false (or 1 2))
                                   (else (or 3 4)))
                            3)

                      (list '(cond (true 1) ((list "hello" "world") => car)) 1)
                      (list '(cond (false 1) ((list "hello" "world") => car)) "hello")
                      (list '(cond (false 1)
                                   ((and (list 1 2) false) => car)
                                   (else 3))
                            3)
                      ))

    ((testsets 'add) "define"
                    (list
                      (list '(begin (define a 1) a) 1)
                      (list '(begin (define b 2) b) 2)
                      (list '(+ a b) 3)
                      (list '(begin
                               (define (add1 n) (+ n 1))
                               (add1 1))
                            2)

                      ; nested-define
                      (list '(begin
                               (define (three)
                                 (define a 1)
                                 (define b 2)
                                 (+ a b))
                               (three))
                            3)
                      (list '(begin
                               (define (odd? n)
                                 (if (= n 0)
                                     false
                                     (even? (- n 1))))
                               (define (even? n)
                                 (if (= n 0)
                                     true
                                     (odd? (- n 1))))
                               (odd? 5))
                            true)
                      ))

    ((testsets 'add) "assignment"
                    (list
                      (list '(begin (define a 0) (set! a 3) a) 3)
                      (list '(begin (define b 0) (set! b 4) b) 4)
                      (list '(+ a b ) 7)
                      (list '(begin (set! a (+ 5 5)) a) 10)
                      ))

    ((testsets 'add) "lambda"
                    (list
                      (list '((lambda (x) (+ x x)) 2) 4)
                      (list '(begin
                               (define double (lambda (x) (+ x x)))
                               (double 4))
                            8)
                      ))

    ((testsets 'add) "let"
                    (list
                      (list '(let ((a 1)) a) 1)
                      (list '(let ((a 1) (b 2)) (+ a b)) 3)
                      (list '(let ((a 1))
                               (let ((b 2))
                                 (+ a b)))
                            3)

                      (list '(let* ((a 1)) a) 1)
                      (list '(let* ((a 1) (b 2)) (+ a b)) 3)
                      (list '(let* ((a 1)
                                    (b (+ a 1)))
                               (+ a b))
                            3)
                      (list '(let* ((a 1)
                                    (b (+ a 1))
                                    (c (+ b 1)))
                               (+ a b c))
                            6)

                      ; named-let
                      (list '(begin
                               (define (fib n)
                                 (let fib-iter ((a 1)
                                                (b 0)
                                                (count n))
                                   (if (= count 0)
                                       b
                                       (fib-iter (+ a b)
                                                 a
                                                 (- count 1)))))
                               (fib 6))
                            8)

                      ; letrec
                      (list '(letrec
                               ((fact (lambda (n)
                                        (if (= 1 n)
                                            1
                                            (* n (fact (- n 1)))))))
                               (fact 5))
                            120)
                      ))


    (testsets 'run)
    'done))

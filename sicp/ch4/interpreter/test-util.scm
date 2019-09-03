(load "../../ch3/25.scm")
(load "logger.scm")

(define logger (make-logger))

(define (make-test test-interface)
  (define (make-testset name testcases)
    (list name (list (length testcases) 0) testcases))
  (define (testset-name t)
    (car t))
  (define (testset-length t)
    (caadr t))
  (define (set-testset-length! t len)
    (set-car! (cadr t) len))
  (define (testset-passed t)
    (cadadr t))
  (define (testset-passed++! t)
    (set-car! (cdadr t) (+ (testset-passed t) 1)))
  (define (set-testset-passed! t val)
    (set-car! (cdadr t) val))
  (define (testset-cases t)
    (caddr t))

  (let ((testsets (make-table 'testsets)))
    (define (get name)
      ((testsets 'lookup) (list name)))
    (define (put name testset)
      ((testsets 'insert!) (list name) testset))

    (define (add-testset name testcases)
      (let ((testset (get name)))
        (if testset
            (put name
                 (make-testset name
                               (append (testset-cases testset)
                                       testcases)))
            (put name
                 (make-testset name testcases)))))

    (define (accumulate op zero-value seq)
      (define (iter remain result)
        (if (null? remain)
            result
            (iter (cdr remain)
                  (op (car remain)
                      result))))
      (iter seq zero-value))

    (define (test-one-set! name)
      (logger 'info "begin to run testset: " (string-upcase name))
      (let* ((testset (get name))
             (testcases (testset-cases testset))
             (passed (accumulate + 0
                                 (map test-single
                                      testcases))))
        (set-testset-passed! testset passed)

        (logger 'info
                "testset: " (string-upcase name) ", "
                (testset-passed testset) "/" (testset-length testset) " passed.")
        (newline))
      'done)

    (define (test-single testcase)
      (define (test-single-ok? testcase)
        ((test-interface 'test) testcase))
      (if (test-single-ok? testcase)
          1
          (begin
            (logger 'warning "testcase failed: ")
            (display ((test-interface 'input) testcase))
            (display ", expect: ")
            (display ((test-interface 'expect) testcase))
            (display ", got: ")
            (display ((test-interface 'got) testcase))
            0)))

    (define (test-all-testsets)
      (let ((keys (map car (testsets 'get-keys))))
        (for-each test-one-set! (reverse keys))))

    (define (total-testcases)
      (accumulate + 0
                  (map (lambda (testset-name)
                         (testset-length (get (car testset-name))))
                       (testsets 'get-keys))))

    (define (total-passed)
      (accumulate + 0
                  (map (lambda (testset-name)
                         (testset-passed (get (car testset-name))))
                       (testsets 'get-keys))))

    (define (run)
      (logger 'info "total testcase to be run: " (total-testcases))
      (newline)

      (test-all-testsets)

      (logger 'info (total-passed) "/" (total-testcases) " passed"))

    (define (dispatch m)
      (cond ((eq? m 'run) (run))
            ((eq? m 'add) add-testset)
            (else (error "Unknown operation for test --" m))))

    dispatch))

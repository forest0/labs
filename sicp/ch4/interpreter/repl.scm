(define (get-repl eval print)
  (define input-prompt "my-repl> ")
  (define (prompt-for-input string)
    (newline)
    (newline)
    (display string))

  (define (driver-loop)
    (prompt-for-input input-prompt)
    (let* ((input (read))
           (result (eval input)))
      (print result)
      (driver-loop)))
  driver-loop)
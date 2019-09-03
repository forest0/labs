(define (make-table . table-name)
  (let ((local-table (if (null? table-name) (list '*table*) table-name))
        (keys (list '*keys*)))

    (define (has-key? key-list)
      (not (false? (member key-list keys))))

    (define (add-key-if-not-exist! key-list)
      (if (not (has-key? key-list))
          (set-cdr! keys (cons key-list (cdr keys)))))

    (define (lookup key-list)
      (define (iter key-list table)
        (let ((cur-key (car key-list))
              (remaining-key (cdr key-list)))
          (let ((record (assoc cur-key (cdr table))))
            (if record
                (if (null? remaining-key)
                    (cdr record)
                    (iter remaining-key record))
                #f))))
      (iter key-list local-table))

    ; ref: https://sicp.readthedocs.io/en/latest/chp3/25.html
    (define (insert! key-list value)
      (define (join-table! new-record table)
        (set-cdr! table
                  (cons new-record (cdr table))))
      (define (iter key-list table value)
        (let ((cur-key (car key-list))
              (remaining-key (cdr key-list)))
          (let ((record (assoc cur-key (cdr table))))
            (cond
              ; 1. 有记录，无剩余关键字
              ;    更新记录的值
              ((and record (null? remaining-key))
               (set-cdr! record value)
               table)

              ; 2. 有记录，有剩余关键字
              ;    递归插入
              ((and record (not (null? remaining-key)))
               (iter remaining-key record value))

              ; 3. 无记录，有剩余关键字
              ;    a. 创建子表
              ;    b. 对子表进行插入
              ;    c. 连接子表
              ((and (not record) (not (null? remaining-key)))
               (join-table! (iter remaining-key (list cur-key) value)
                            table)
               table)

              ; 4. 无记录，无剩余关键字
              ;    创建记录并连接到当前表
              (else
                (join-table! (cons cur-key value) table)
                table)))))
        (iter key-list local-table value)
        (add-key-if-not-exist! key-list)
      'ok)
    (define (dispatch m)
      (cond ((eq? m 'lookup) lookup)
            ((eq? m 'insert!) insert!)
            ((eq? m 'get-table) local-table)
            ((eq? m 'get-keys) (cdr keys))
            (else (error "Unknown operation -- DISPATCH of table" m))))
    dispatch))

#!/usr/bin/env bash

function check_validity(){
  # 文件数目检查
  if [ $(ls -l | grep system.log | wc -l) != $NODE_NUM ]; then
    echo "前缀为system.log的日志文件数和节点数目应该相等"
    exit 1
  fi
  echo "################ 日志预处理中 ################"
  # 缩减日志规模
  startString="attempt enter new height to ($((BEGIN_HEIGHT-1)))"
  endString="commit block \[$((END_HEIGHT+1))"

  # shellcheck disable=SC2045
  for file in `ls system.log.*`
  do
    if [[ $file == system.log.* ]]; then
      prune_node_log "$file" "$startString" "$endString" &
    fi
  done
  wait
  echo "###################################################"

  echo "################ 日志有效性检查中 ################"
  # 提交节点是否参与共识和提交区块
  for i in $(seq $BEGIN_HEIGHT $END_HEIGHT)
  do
    check_block "$i"
  done
  # 删除临时文件
  for i in $(seq $BEGIN_HEIGHT $END_HEIGHT)
  do
    rm -rf $i
  done
  rm -rf final
  echo "###################################################"
}

function prune_node_log() {
   fileName=${1}
   startStr=${2}
   endStr=${3}
   echo "-------- 日志: "$fileName" 过滤中--------"
   # 检索行号
   startLine=`grep -wn "$startStr" $fileName | awk -F: '{print $1}'`
   endLine=`grep -wn "$endStr" $fileName | awk -F: '{print $1}'`
   # 过滤掉无用日志
   if [ ! -z ${startLine} ] && [ ! -z ${endLine} ];then
     sed  '1,'$startLine'd;'$endLine',$d'  $fileName > $fileName"_bak"
     rm -rf  $fileName
     mv $fileName"_bak" $fileName
   fi
   echo "-------- 日志: "$fileName" 过滤完成--------"
}

function check_block(){
  height=${1}
  # 提交节点是否参与共识和提交区块
  if [ $(grep "attempt enter new height to ($height)" system.log.* | wc -l) != $NODE_NUM ]; then
    echo "某节点未参与共识 $height"
    exit 1
  fi
  if [ $(grep "commit block \[$height" system.log.* | wc -l) != $NODE_NUM ]; then
    echo "某节点未提交区块 $height"
    exit 1
  fi
  echo "-------- 区块: "$height" 日志有效 --------"
}

function set_key() {
  # 操作入口模块名
   txpool_module="txpool_"
   core_gen_module="core_gen_"
   core_verify_module="core_verify_"
   core_commit_module="core_commit_"
   consensus_module="consensus_"
   consensus_wal_module="consensus_wal_"
   storage_module="storage_"
   # 具体操作名
   fetch="fetch:"
   prune="prune:"
   cache="cache:"
   remove="remove:"
   total="total:"
   filter="filter:"
   begin_DB_transaction="begin DB transaction:"
   new_snapshort="new snapshot:"
   vm="vm:"
   finalize_block="finalize block:"
   signBlock="signBlock:"
   signProposal="signProposal:"
   verify="verify:"
   blockSig="blockSig:"
   get="get:"
   txVerify="txVerify:"
   txRoot="txRoot:"
   pool="pool:"
   consensusCheckUsed="consensusCheckUsed:"
   marshalData="marshalData:"
   marshalEntry="marshalEntry:"
   saveWal="saveWal:"
   Proposal="Proposal:"
   Prevote="Prevote:"
   Precommit="Precommit:"
   marshal="marshal: "
   writeFile="writeFile: "
   writeCache="writeCache: "
   writeBatchChan="writeBatchChan: "     #  存储quick快速写模式下的日志
   writeKvDB="writeKvDB: "              #  存储common普通写模式下的日志
   total2="total: "
   check="check:"
   db="db:"
   ss="ss:"
   conf="conf:"
   pubConEvent="pubConEvent:"
   other="other:"
   interval="interval:"

   # 按序排列输出最终结果
   # 主节点
   key_logs_proposer1_avg=(
   "$txpool_module""$fetch"
   "$txpool_module""$prune"
   "$txpool_module""$cache"
   "$txpool_module""$remove"
   "$txpool_module""$total"

   "$core_gen_module""$fetch"
   "$core_gen_module""$filter"
   "$core_gen_module""$begin_DB_transaction"
   "$core_gen_module""$new_snapshort"
   "$core_gen_module""$vm"
   "$core_gen_module""$finalize_block"
   "$core_gen_module""$total"

   "$consensus_module""$signBlock"
   "$consensus_module""$signProposal"
   "$consensus_module""$total"

   "$consensus_module""$Proposal"
   )
    # 从节点
    key_logs_backup2_avg=(
   "$consensus_module""$verify"

   "$core_verify_module""$blockSig"
   "$core_verify_module""$vm"
   "$txpool_module""$get"
#   "$txpool_module""$prune"
   "$txpool_module""$remove"
#   "$txpool_module""$total"
   "$core_verify_module""$txVerify"
   "$core_verify_module""$txRoot"
   "$core_verify_module""$pool"
   "$core_verify_module""$consensusCheckUsed"
   "$core_verify_module""$total"

   "$consensus_module""$Prevote"
   )
   # 主从节点
   key_logs_all3_tmp=(
   "$consensus_wal_module""$marshalData"
   "$consensus_wal_module""$marshalEntry"
   "$consensus_wal_module""$saveWal"
   "$consensus_wal_module""$total"
   "$consensus_module""$Precommit"

   "$storage_module""$(echo $marshal | sed 's/[ \t]*$//g')"
   "$storage_module""$(echo $writeFile | sed 's/[ \t]*$//g')"
   "$storage_module""$(echo $writeCache | sed 's/[ \t]*$//g')"
   "$storage_module""$(echo $writeBatchChan | sed 's/[ \t]*$//g')"
   "$storage_module""$(echo $writeKvDB | sed 's/[ \t]*$//g')"
   "$storage_module""$(echo $total | sed 's/[ \t]*$//g')"

   "$core_commit_module""$check"
   "$core_commit_module""$db"
   "$core_commit_module""$ss"
   "$core_commit_module""$conf"
   "$core_commit_module""$pool"
   "$core_commit_module""$pubConEvent"
   "$core_commit_module""$filter"
   "$core_commit_module""$other"
   "$core_commit_module""$total"
   "$core_commit_module""$interval"
   )

}

function checkout_times() {
  echo "################ 各区块，具体耗时分析中 ################"
  for height in $(seq $BEGIN_HEIGHT $END_HEIGHT)
  do
    checkout_a_block_time "$height" &
  done
  wait
  echo "######################################################"
}

function checkout_a_block_time() {
  height=${1}
  echo "-------- 区块: "$height" 耗时分析中 --------"
  # 创建高度目录，该区块所有的分析文件都在该目录中
  mkdir $height
  # 在一轮共识流程中，对每个节点分别进行各个部分操作的具体耗时的提取
  # shellcheck disable=SC2045
  for file in `ls system.log.*`
  do
    if [[ $file == system.log.* ]]; then
      grep_key_log_and_checkout_time "$file" "$height"
    fi
  done
  echo "-------- 区块: "$height" 耗时分析完成 --------"
}

function grep_key_log_and_checkout_time(){
   # 传入日志路径和高度
   log_path=${1}
   height=${2}
   # 关键日志
   # 主从节点
   enter_new_height="attempt enter new height to ($height)"
   # 主节点
   is_proposer="($height/0/PROPOSE) sendProposeState isProposer: true"
   gen_block="proposer success \[$height]"
   fetch_txs="FetchTxs, height:$height"             # single normal交易池
   fetch_batches="FetchTxBatches, height:$height"   # batch交易池
   gen_proposal="($height/0/PROPOSE) generated proposal"
   # 从节点
   pro_proposal="($height/0/PROPOSE) processed proposal"
   pro_verify_res="processed verify result ($height/"
   get_txs="GetAllTxsByBatchIds, height:$height,"
   verify_block="verify success \[$height,"
   # 主从节点
   add_vote_proposal="($height/0/PROPOSE) add vote"
   add_vote_prevote="($height/0/PREVOTE) add vote"
   add_vote_precommit="($height/0/PRECOMMIT) add vote"
   enter_prevote="($height/0/PROPOSE) enter prevote"
   enter_precommit="($height/0/PREVOTE) enter precommit"
   consensus_save_wal="($height/0/PRECOMMIT) consensus save wal"
   enter_commit="($height/0/PRECOMMIT) enter commit"
   consensus_cost="consensus cost: {\"Height\":$height,"
   put_block_quick="put block\[$height] quick"
   put_block_common="put block\[$height] common"
   commit_block="commit block \[$height]"

   key_logs=(
   "$enter_new_height"
   "$is_proposer"
   "$fetch_txs"
   "$fetch_batches"
   "$gen_block"
   "$gen_proposal"
   "$pro_proposal"
   "$get_txs"
   "$verify_block"
   "$pro_verify_res"
   "$add_vote_proposal"
   "$add_vote_prevote"
   "$add_vote_precommit"
   "$enter_prevote"
   "$enter_precommit"
   "$consensus_save_wal"
   "$enter_commit"
   "$consensus_cost"
   "$put_block_quick"
   "$put_block_common"
   "$commit_block"
   )

   # grep 关键日志到临时文件, 文件名 324251_system.log.1
   grepped_log_path=$height/$height"_"$log_path
   for keylog in "${key_logs[@]}";do
     grep -a "$keylog" $log_path >> $grepped_log_path
   done

   # 默认时间单位 ms
   defaultUnit="ms"

   # 主节点日志分析, 文件名 324251_proposer_avg
   if [ `grep -c "$is_proposer" $grepped_log_path` -ne '0' ];then
     proposer_log_path=$height/$height"_proposer_avg"
     fetch_txs_flag="FetchTxs,"
     fetch_batches_flag="FetchTxBatches,"
     gen_block_flag="proposer success"
     gen_proposal_flag="generated proposal"
     consensus_save_wal_flag="consensus save wal,"
     consensus_cost_flag="consensus cost:"
     put_block_flag="put block"
     commit_block_flag="commit block"
     while read line
     do
       if [[ $line =~ $fetch_txs_flag ]]; then
         str=$"TxPool获取交易":${line#*$fetch_txs_flag}
         checkoutTime "$txpool_module" "$str" "$fetch" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$txpool_module" "$str" "$prune" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$txpool_module" "$str" "$cache" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$txpool_module" "$str" "$total" "$defaultUnit" >> $proposer_log_path

       elif [[ $line =~ $fetch_batches_flag ]]; then
         str=$"TxPool获取交易":${line#*$fetch_batches_flag}
         checkoutTime "$txpool_module" "$str" "$fetch" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$txpool_module" "$str" "$prune" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$txpool_module" "$str" "$cache" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$txpool_module" "$str" "$remove" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$txpool_module" "$str" "$total" "$defaultUnit" >> $proposer_log_path

       elif [[ $line =~ $gen_block_flag ]]; then
         str=$"Core构造区块":${line#*$gen_block_flag}
         checkoutTime "$core_gen_module" "$str" "$fetch" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$core_gen_module" "$str" "$filter" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$core_gen_module" "$str" "$begin_DB_transaction" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$core_gen_module" "$str" "$new_snapshort" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$core_gen_module" "$str" "$vm" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$core_gen_module" "$str" "$finalize_block" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$core_gen_module" "$str" "$total" "$defaultUnit" >> $proposer_log_path

       elif [[ $line =~ $gen_proposal_flag ]]; then
         str=$"Consensus构造提案":${line#*$gen_proposal_flag}
         checkoutTime "$consensus_module" "$str" "$signBlock" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$consensus_module" "$str" "$signProposal" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$consensus_module" "$str" "$total" "$defaultUnit" >> $proposer_log_path

       elif [[ $line =~ $consensus_save_wal_flag ]]; then
         str=$"Consensus写Wal":${line#*$consensus_save_wal_flag}
         checkoutTime "$consensus_wal_module" "$str" "$marshalData" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$consensus_wal_module" "$str" "$marshalEntry" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$consensus_wal_module" "$str" "$saveWal" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$consensus_wal_module" "$str" "$total" "$defaultUnit" >> $proposer_log_path

       elif [[ $line =~ $consensus_cost_flag ]]; then
         str=$(echo $"Consensus各阶段耗时":${line#*$consensus_cost_flag} | sed 's/\"//g')
         getProposalUnit "$str" \
         && checkoutTime "$consensus_module" "$str" "$Proposal" "$CONSENSUSUNIT" >> $proposer_log_path \
         && getPrevoteUnit "$str" \
         && checkoutTime "$consensus_module" "$str" "$Prevote" "$CONSENSUSUNIT" >> $proposer_log_path \
         && getPrecommitUnit "$str" \
         && checkoutTime "$consensus_module" "$str" "$Precommit" "$CONSENSUSUNIT" >> $proposer_log_path

       elif [[ $line =~ $put_block_flag ]]; then
         str=$"Store落库":${line#*$put_block_flag}
         if [[ $str =~ "quick" ]]; then
            checkoutTime "$storage_module" "$str" "$marshal" "$defaultUnit" >> $proposer_log_path \
            && checkoutTime "$storage_module" "$str" "$writeFile" "$defaultUnit" >> $proposer_log_path \
            && checkoutTime "$storage_module" "$str" "$writeCache" "$defaultUnit" >> $proposer_log_path \
            && checkoutTime "$storage_module" "$str" "$writeBatchChan" "$defaultUnit" >> $proposer_log_path \
            && checkoutTime "$storage_module" "$str" "$total2" "$defaultUnit" >> $proposer_log_path
         else
            checkoutTime "$storage_module" "$str" "$marshal" "$defaultUnit" >> $proposer_log_path \
            && checkoutTime "$storage_module" "$str" "$writeFile" "$defaultUnit" >> $proposer_log_path \
            && checkoutTime "$storage_module" "$str" "$writeCache" "$defaultUnit" >> $proposer_log_path \
            && checkoutTime "$storage_module" "$str" "$writeKvDB" "$defaultUnit" >> $proposer_log_path \
            && checkoutTime "$storage_module" "$str" "$total2" "$defaultUnit" >> $proposer_log_path
         fi
       elif [[ $line =~ $commit_block_flag ]]; then
         str=$"Core提交区块":${line#*$commit_block_flag}
         checkoutTime "$core_commit_module" "$str" "$check" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$core_commit_module" "$str" "$db" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$core_commit_module" "$str" "$ss" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$core_commit_module" "$str" "$conf" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$core_commit_module" "$str" "$pool" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$core_commit_module" "$str" "$pubConEvent" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$core_commit_module" "$str" "$filter" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$core_commit_module" "$str" "$other" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$core_commit_module" "$str" "$total" "$defaultUnit" >> $proposer_log_path \
         && checkoutTime "$core_commit_module" "$str" "$interval" "$defaultUnit" >> $proposer_log_path
       fi
     done < $grepped_log_path
   # 从节点日志分析, 文件名 324251_system.log.1_backup
   else
     backup_log_path=$grepped_log_path"_backup"
     pro_proposal_flag="processed proposal"
     get_txs_flag="GetAllTxsByBatchIds,"
     verify_block_flag="verify success"
     pro_verify_res_flag="processed verify result"
     consensus_save_wal_flag="consensus save wal,"
     consensus_cost_flag="consensus cost:"
     put_block_flag="put block"
     commit_block_flag="commit block"
     while read line
     do
       if [[ $line =~ $pro_proposal_flag ]]; then
         str=$"Consensus处理提案":${line#*$pro_proposal_flag}
         checkoutTime "$consensus_module" "$str" "$verify" "$defaultUnit" >> $backup_log_path

       elif [[ $line =~ $get_txs_flag ]]; then
         str=$"TxPool载入交易":${line#*$get_txs_flag}
         checkoutTime "$txpool_module" "$str" "$get" "$defaultUnit" >> $backup_log_path \
         && checkoutTime "$txpool_module" "$str" "$prune" "$defaultUnit" >> $backup_log_path \
         && checkoutTime "$txpool_module" "$str" "$remove" "$defaultUnit" >> $backup_log_path \
         && checkoutTime "$txpool_module" "$str" "$total" "$defaultUnit" >> $backup_log_path

       elif [[ $line =~ $verify_block_flag ]]; then
         str=$"Core验证区块":${line#*$verify_block_flag}
         checkoutTime "$core_verify_module" "$str" "$blockSig" "$defaultUnit" >> $backup_log_path \
         && checkoutTime "$core_verify_module" "$str" "$vm" "$defaultUnit" >> $backup_log_path \
         && checkoutTime "$core_verify_module" "$str" "$txVerify" "$defaultUnit" >> $backup_log_path \
         && checkoutTime "$core_verify_module" "$str" "$txRoot" "$defaultUnit" >> $backup_log_path \
         && checkoutTime "$core_verify_module" "$str" "$pool" "$defaultUnit" >> $backup_log_path \
         && checkoutTime "$core_verify_module" "$str" "$consensusCheckUsed" "$defaultUnit" >> $backup_log_path \
         && checkoutTime "$core_verify_module" "$str" "$total" "$defaultUnit" >> $backup_log_path

       elif [[ $line =~ $consensus_save_wal_flag ]]; then
         str=$"Consensus写Wal":${line#*$consensus_save_wal_flag}
         checkoutTime "$consensus_wal_module" "$str" "$marshalData" "$defaultUnit" >> $backup_log_path \
         && checkoutTime "$consensus_wal_module" "$str" "$marshalEntry" "$defaultUnit" >> $backup_log_path \
         && checkoutTime "$consensus_wal_module" "$str" "$saveWal" "$defaultUnit" >> $backup_log_path \
         && checkoutTime "$consensus_wal_module" "$str" "$total" "$defaultUnit" >> $backup_log_path

       elif [[ $line =~ $consensus_cost_flag ]]; then
         str=$(echo $"Consensus各阶段耗时":${line#*$consensus_cost_flag} | sed 's/\"//g')
         getProposalUnit "$str" \
         && checkoutTime "$consensus_module" "$str" "$Proposal" "$CONSENSUSUNIT" >> $backup_log_path \
         && getPrevoteUnit "$str" \
         && checkoutTime "$consensus_module" "$str" "$Prevote" "$CONSENSUSUNIT" >> $backup_log_path \
         && getPrecommitUnit "$str" \
         && checkoutTime "$consensus_module" "$str" "$Precommit" "$CONSENSUSUNIT" >> $backup_log_path

       elif [[ $line =~ $put_block_flag ]]; then
         str=$"Store落库":${line#*$put_block_flag}
         if [[ $str =~ "quick" ]]; then
           checkoutTime "$storage_module" "$str" "$marshal" "$defaultUnit" >> $backup_log_path \
           && checkoutTime "$storage_module" "$str" "$writeFile" "$defaultUnit" >> $backup_log_path \
           && checkoutTime "$storage_module" "$str" "$writeCache" "$defaultUnit" >> $backup_log_path \
           && checkoutTime "$storage_module" "$str" "$writeBatchChan" "$defaultUnit" >> $backup_log_path \
           && checkoutTime "$storage_module" "$str" "$total2" "$defaultUnit" >> $backup_log_path
         else
           checkoutTime "$storage_module" "$str" "$marshal" "$defaultUnit" >> $backup_log_path \
           && checkoutTime "$storage_module" "$str" "$writeFile" "$defaultUnit" >> $backup_log_path \
           && checkoutTime "$storage_module" "$str" "$writeCache" "$defaultUnit" >> $backup_log_path \
           && checkoutTime "$storage_module" "$str" "$writeKvDB" "$defaultUnit" >> $backup_log_path \
           && checkoutTime "$storage_module" "$str" "$total2" "$defaultUnit" >> $backup_log_path
         fi
       elif [[ $line =~ $commit_block_flag ]]; then
         str=$"Core提交区块":${line#*$commit_block_flag}
         checkoutTime "$core_commit_module" "$str" "$check" "$defaultUnit" >> $backup_log_path \
         && checkoutTime "$core_commit_module" "$str" "$db" "$defaultUnit" >> $backup_log_path \
         && checkoutTime "$core_commit_module" "$str" "$ss" "$defaultUnit" >> $backup_log_path \
         && checkoutTime "$core_commit_module" "$str" "$conf" "$defaultUnit" >> $backup_log_path \
         && checkoutTime "$core_commit_module" "$str" "$pool" "$defaultUnit" >> $backup_log_path \
         && checkoutTime "$core_commit_module" "$str" "$pubConEvent" "$defaultUnit" >> $backup_log_path \
         && checkoutTime "$core_commit_module" "$str" "$filter" "$defaultUnit" >> $backup_log_path \
         && checkoutTime "$core_commit_module" "$str" "$other" "$defaultUnit" >> $backup_log_path \
         && checkoutTime "$core_commit_module" "$str" "$total" "$defaultUnit" >> $backup_log_path \
         && checkoutTime "$core_commit_module" "$str" "$interval" "$defaultUnit" >> $backup_log_path
       fi
     done < $grepped_log_path
   fi
}

function checkoutTime(){
   # 模块名 txpool_
   module=${1}
   # 被检索语句
   str=${2}
   # 耗时关键字，构建正则表达式
   key=${3}
   regex=".*"${key}"([0-9]+).*"
   unit=${4}
   # 检索出数值
   num=$(echo "$str"|gawk '{print gensub("'"$regex"'","\\1","1")}')
   # 去掉操作key的末尾空格
   # shellcheck disable=SC2001
   key=$(echo $key | sed 's/[ \t]*$//g')
   # 根据传入的单位，输出操作及耗时 txpool_fetch:14
   if [[ $unit == "ms" ]] ; then
      val=$((num*1))
      echo "$module""$key""$val"
    elif [[ $unit == "s" ]] ; then
      val=$((num*1000))
      echo "$module""$key""$val"
    elif [[ $unit == "µs" ]] ; then
      val=$((num/1000))
      echo "$module""$key""$val"
    else
       val=$((num/1000/1000)) # ns
      echo "$module""$key""$val"
    fi
}

function getProposalUnit(){
  str=${1}
  pruneStr=${str%",Prevote"*}
  regex=".*[0-9]({s,ms,µs,ns}+)*"
  CONSENSUSUNIT=$(echo "$pruneStr"|gawk '{print gensub("'"$regex"'","\\1","1")}')
}

function getPrevoteUnit(){
  str=${1}
  pruneStr=${str%",Precommit"*}
  regex=".*[0-9]({s,ms,µs,ns}+)*"
  CONSENSUSUNIT=$(echo "$pruneStr"|gawk '{print gensub("'"$regex"'","\\1","1")}')
}

function getPrecommitUnit(){
  str=${1}
  pruneStr=${str%",PersistStateDurations"*}
  regex=".*[0-9]({s,ms,µs,ns}+)*"
  CONSENSUSUNIT=$(echo "$pruneStr"|gawk '{print gensub("'"$regex"'","\\1","1")}')
}

function calc_times() {
  echo "################ 各区块，具体耗时计算中 ################"
  for height in $(seq $BEGIN_HEIGHT $END_HEIGHT)
  do
    echo "-------- 区块: "$height" 各操作耗时计算完成--------"
    # 进入目录
    cd $height > /dev/null
    calc_block_time
    cd - > /dev/null
  done
  echo "######################################################"
}

function calc_block_time() {
  # 主节点平均耗时已经存在， 在324251_proposer_avg 文件
  proposer_avg_path=$height"_proposer_avg"
  # 计算从节点的平均耗时, 产生324251_backup_avg 文件
  backup_avg_path=$height"_backup_avg"
  cat *_backup |awk -F":" '{sum[$1]+=$2;a[$1]++}END{for(c in sum){printf("%s:%d\n", c,sum[c]/a[c])}}' > $backup_avg_path
  # 主从节点耗时，部分需要取平均值，产生324251_tmp 文件
  tmp_path=$height"_tmp"
  cat *_avg |awk -F":" '{sum[$1]+=$2;a[$1]++}END{for(c in sum){printf("%s:%d\n", c,sum[c]/a[c])}}' > $tmp_path
  # 汇总主从节点耗时，产生324251_final 文件
  final_path=$height"_final"
  for keylog in "${key_logs_proposer1_avg[@]}";do
    grep "$keylog" $proposer_avg_path >> $final_path
  done
  for keylog in "${key_logs_backup2_avg[@]}";do
    grep "$keylog" $backup_avg_path >> $final_path
  done
  for keylog in "${key_logs_all3_tmp[@]}";do
    grep "$keylog" $tmp_path >> $final_path
  done
}

function count_times() {
  # 存储最终结果
  mkdir final
  for height in $(seq $BEGIN_HEIGHT $END_HEIGHT)
  do
    block_time_file=$height/$height"_final"
    cp -f $block_time_file ./final/
  done
  # 进入到final目录
  cd final
  # 计算最终平均耗时,生成tmp文件
  tmp_file="tmp"
  cat *_final | awk -F":" '{sum[$1]+=$2;a[$1]++}END{for(c in sum){printf("%s:%d\n", c,sum[c]/a[c])}}' > $tmp_file
  # 序列规整，生成final_result_temp文件
  final_temp_file="final_result_temp"
  for keylog in "${key_logs_proposer1_avg[@]}";do
    grep "$keylog" $tmp_file >> $final_temp_file
  done
  for keylog in "${key_logs_backup2_avg[@]}";do
    grep "$keylog" $tmp_file >> $final_temp_file
  done
  for keylog in "${key_logs_all3_tmp[@]}";do
    grep "$keylog" $tmp_file >> $final_temp_file
  done
  # 格式规整，生成final_result文件
  perfect_result="final_result"
  awk -F ":" '{printf "%-35s%-15s\n",$1,$2}' $final_temp_file > $perfect_result
  rm -rf $tmp_file
  rm -rf $final_temp_file
  # 添加子块具体耗时
  for height in $(seq $BEGIN_HEIGHT $END_HEIGHT)
  do
    cat $perfect_result > $height"_temp_final"
    cat $height"_final" | awk -F ":" '{print $2}' > $height"_val"
    paste $height"_temp_final" $height"_val" > $perfect_result
    rm -rf $height"_val"
  done
  # 打印最终分析结果
  echo "###############################################################################################################"
  echo "                        耗时分析结果   单位:ms  区块范围: $BEGIN_HEIGHT-$END_HEIGHT            "
  echo "###############################################################################################################"
  printf "%-36s%-25s%-20s\n" "具体操作" "平均耗时" "各高度区块耗时......"
  cat $perfect_result
  echo "###############################################################################################################"
   # 删除临时文件
  cd ..
  for i in $(seq $BEGIN_HEIGHT $END_HEIGHT)
  do
    rm -rf $i
  done
  rm -rf final
}

function backup_log() {
  log_bak="log_bak"
  mkdir log_bak
  cp system.log* log_bak
  echo "################ 日志备份完成 ################"
}

function recovery_log() {
  log_bak="log_bak"
  rm -rf system.log*
  mv log_bak/* ./
  rm -rf log_bak
}

function time_consuming_count(){
  # 备份日志
  backup_log
  # 日志有效性检查，并过滤无效日志
  check_validity
  # 设置操作关键字, 全局使用
  set_key
  # 提取各高度区块，在一轮共识中，所有操作的具体耗时
  checkout_times
  # 计算各高度区块，在一轮共识中，主从节点各具体操作的耗时
  calc_times
  # 汇总所有区块的耗时，计算平均值
  count_times
  # 恢复日志
  recovery_log
}

# ======================================================================================================================
# 1.脚本和日志需要放入同级目录
# 2.日志命名规范为system.log.n，其中n是节点序号，1，2，3，4，..., n
# ======================================================================================================================

# 第一个参数是共识节点总数
NODE_NUM=$1
# 第二个参数是分析的起始区块高度
BEGIN_HEIGHT=$2
# 第三个参数是分析的结束区块高度
END_HEIGHT=$3

time_consuming_count
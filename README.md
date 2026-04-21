# 26pbl-group8

## Branch Protection Rules (main)
mainブランチは以下のルールで保護されています。
### ■ Rules
- Require a pull request before merging
- Require approvals
  - Required approvals: 1
- Require approval of the most recent reviewable push
- Dismiss stale pull request approvals when new commits are pushed
- Require conversation resolution before merging
- Do not allow bypassing the above settings

---

## ■ Development Flow
このリポジトリでは以下のフローで開発を行います。
1. featureブランチを作成する  
   例：`feature/login-function`
2. 作業後、Pull Requestを作成する（mainへ直接pushは禁止）
3. 他メンバーがレビュー（1人以上）
4. 修正があれば対応
5. 承認後、mainへマージ

---

## ■ Notes
- mainブランチへの直接pushは禁止
- 必ずPull Requestを経由すること
- レビュー後に変更を加えた場合は、再レビューが必要
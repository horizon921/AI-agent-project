import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional
import shutil


class FeedbackSystem:
    def __init__(self):
        """初始化反馈系统"""
        # 🔥 统一使用 data_file，移除所有 feedback_file 引用
        current_file = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file)
        project_root = os.path.dirname(os.path.dirname(current_dir))

        print(f"🔧 当前文件: {current_file}")
        print(f"🔧 当前目录: {current_dir}")
        print(f"🔧 项目根目录: {project_root}")

        # 数据目录和文件路径
        self.data_dir = os.path.join(project_root, "data")
        self.data_file = os.path.join(self.data_dir, "feedback_data.json")

        print(f"🔧 数据文件路径: {self.data_file}")
        print(f"📂 当前工作目录: {os.getcwd()}")

        # 确保数据目录存在
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            print(f"📁 创建数据目录: {self.data_dir}")
        else:
            print(f"✅ 数据目录已存在: {self.data_dir}")

        # 初始化数据文件
        self._init_data_file()

    def _init_data_file(self):
        """初始化数据文件"""
        if not os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
                print(f"📄 创建反馈数据文件: {self.data_file}")
            except Exception as e:
                print(f"❌ 创建数据文件失败: {e}")
        else:
            print(f"✅ 反馈数据文件已存在: {self.data_file}")

    def init_session_state(self):
        """初始化session state"""
        if 'feedback_data' not in st.session_state:
            st.session_state.feedback_data = self._load_feedback_data()

        if 'interaction_feedback' not in st.session_state:
            st.session_state.interaction_feedback = {}

    def _load_feedback_data(self) -> List[Dict]:
        """从文件加载反馈数据"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        print(f"✅ 读取到 {len(data)} 条现有反馈")
                        return data
                    else:
                        print("📭 数据文件为空")
                        return []
            else:
                print(f"📄 数据文件不存在: {self.data_file}")
                return []
        except Exception as e:
            print(f"❌ 读取反馈数据失败: {e}")
            return []

    def _save_feedback_data(self, data: List[Dict]) -> bool:
        """保存反馈数据到文件"""
        try:
            # 创建备份
            if os.path.exists(self.data_file):
                backup_file = f"{self.data_file}.backup"
                shutil.copy2(self.data_file, backup_file)
                print(f"📋 创建备份: {backup_file}")

            # 保存数据
            print(f"🔥 准备写入 {len(data)} 条数据")
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"✅ 反馈数据已保存到: {self.data_file}")

            # 验证保存
            file_size = os.path.getsize(self.data_file)
            print(f"📁 文件大小: {file_size} bytes")

            # 验证数据完整性
            with open(self.data_file, 'r', encoding='utf-8') as f:
                verification_data = json.load(f)
                if len(verification_data) == len(data):
                    print(f"✅ 验证成功，文件包含 {len(verification_data)} 条记录")
                    return True
                else:
                    print(
                        f"❌ 验证失败，期望 {len(data)} 条，实际 {len(verification_data)} 条")
                    return False

        except Exception as e:
            print(f"❌ 保存反馈数据失败: {e}")
            return False

    def submit_feedback(self, interaction_id: str, feedback_data: Dict[str, Any]) -> bool:
        """提交反馈数据"""
        print(f"🔥 开始提交反馈: {interaction_id}")
        print(f"🔥 反馈数据: {feedback_data}")

        try:
            # 确保数据目录存在
            print(f"🔥 数据目录: {self.data_dir}")
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir)
                print(f"📁 创建数据目录: {self.data_dir}")
            else:
                print(f"✅ 数据目录已存在: {self.data_dir}")

            # 检查数据文件
            print(f"🔥 数据文件路径: {self.data_file}")
            print(f"🔥 文件是否存在: {os.path.exists(self.data_file)}")

            # 加载现有数据
            existing_data = self._load_feedback_data()

            # 创建新的反馈记录
            new_feedback = {
                'interaction_id': interaction_id,
                'timestamp': datetime.now().isoformat(),
                'feedback_type': st.session_state.get('current_app_mode', '未知'),
                'session_id': st.session_state.get('session_id', 'unknown'),
                **feedback_data
            }

            # 计算平均评分
            if 'ratings' in feedback_data and feedback_data['ratings']:
                ratings = feedback_data['ratings']
                avg_rating = sum(ratings.values()) / len(ratings)
                new_feedback['average_rating'] = round(avg_rating, 2)

            print(f"🔥 新反馈数据: {new_feedback}")

            # 检查是否已存在相同的反馈
            existing_ids = [item.get('interaction_id')
                            for item in existing_data]
            if interaction_id in existing_ids:
                print(f"🔄 更新现有反馈: {interaction_id}")
                for i, item in enumerate(existing_data):
                    if item.get('interaction_id') == interaction_id:
                        existing_data[i] = new_feedback
                        break
            else:
                print(f"➕ 添加新反馈: {interaction_id}")
                existing_data.append(new_feedback)

            # 保存到文件
            if self._save_feedback_data(existing_data):
                # 更新session state
                st.session_state.feedback_data = existing_data
                st.session_state.interaction_feedback[interaction_id] = {
                    'submitted': True,
                    'timestamp': datetime.now().isoformat()
                }

                print(f"📊 当前总反馈数: {len(existing_data)}")
                return True
            else:
                print("❌ 数据保存失败")
                return False

        except Exception as e:
            print(f"❌ 提交反馈失败: {e}")
            import traceback
            print(f"🔍 错误详情: {traceback.format_exc()}")
            return False

    def generate_interaction_id(self) -> str:
        """生成唯一的交互ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"interaction_{timestamp}"

    def show_feedback_form(self, interaction_id: str):
        """显示反馈表单"""
        feedback_key = f"feedback_{interaction_id}"

        # 检查是否已经提交过反馈
        if st.session_state.get(feedback_key, {}).get('submitted', False):
            st.success("✅ 已提交反馈，谢谢您的评价！")
            return

        # 反馈维度配置
        feedback_dimensions = {
            'accuracy': '准确性',
            'helpfulness': '有用性',
            'clarity': '清晰度',
            'completeness': '完整性'
        }

        with st.form(key=f"feedback_form_{interaction_id}"):
            st.markdown("#### 📊 请为这次回答评分")

            ratings = {}
            cols = st.columns(len(feedback_dimensions))

            for i, (key, label) in enumerate(feedback_dimensions.items()):
                with cols[i]:
                    rating = st.select_slider(
                        label,
                        options=[1, 2, 3, 4, 5],
                        value=3,
                        format_func=lambda x: "⭐" * x,
                        key=f"{feedback_key}_{key}"
                    )
                    ratings[key] = rating

            # 文字评论
            comment = st.text_area(
                "💬 补充评论（可选）",
                placeholder="请分享您的想法和建议...",
                key=f"{feedback_key}_comment",
                height=80
            )

            # 提交按钮
            submitted = st.form_submit_button(
                "提交反馈",
                type="primary",
                use_container_width=True
            )

            if submitted:
                # 准备反馈数据
                current_feedback = {
                    'ratings': ratings,
                    'comment': comment.strip() if comment else None
                }

                # 🔥 确保调用的是 submit_feedback 方法（没有下划线）
                success = self.submit_feedback(
                    interaction_id, current_feedback)

                if success:
                    # 标记为已提交
                    st.session_state[feedback_key] = {
                        'submitted': True,
                        'timestamp': datetime.now().isoformat(),
                        'data': current_feedback
                    }

                    st.success("✅ 反馈提交成功，谢谢您的评价！")
                    st.rerun()
                else:
                    st.error("❌ 反馈提交失败，请稍后重试")

    def show_feedback_stats(self):
        """显示反馈统计"""
        try:
            feedback_data = st.session_state.get('feedback_data', [])

            if not feedback_data:
                st.info("📭 暂无反馈数据")
                return

            # 基本统计
            total_feedback = len(feedback_data)

            # 计算平均评分
            ratings = []
            for feedback in feedback_data:
                if 'average_rating' in feedback:
                    ratings.append(feedback['average_rating'])
                elif 'ratings' in feedback and feedback['ratings']:
                    avg = sum(feedback['ratings'].values()
                              ) / len(feedback['ratings'])
                    ratings.append(avg)

            avg_rating = sum(ratings) / len(ratings) if ratings else 0

            # 显示统计信息
            col1, col2 = st.columns(2)
            with col1:
                st.metric("总反馈数", total_feedback)
            with col2:
                st.metric(
                    "平均评分", f"{avg_rating:.1f}/5.0" if avg_rating > 0 else "暂无")

            # 评分分布
            if ratings:
                rating_counts = {}
                for rating in ratings:
                    rounded = round(rating)
                    rating_counts[rounded] = rating_counts.get(rounded, 0) + 1

                st.markdown("**评分分布:**")
                for i in range(5, 0, -1):
                    count = rating_counts.get(i, 0)
                    percentage = (count / len(ratings)) * 100 if ratings else 0
                    st.write(f"{'⭐' * i} {count} 条 ({percentage:.1f}%)")

        except Exception as e:
            st.error(f"❌ 显示统计失败: {e}")

    def force_refresh_data(self):
        """强制刷新反馈数据"""
        print("🔄 强制刷新反馈数据...")

        # 清除 session state 中的缓存数据
        if 'feedback_data' in st.session_state:
            del st.session_state.feedback_data
        if 'interaction_feedback' in st.session_state:
            del st.session_state.interaction_feedback

        # 重新初始化
        self.init_session_state()

        print("✅ 反馈数据已刷新")

    def export_feedback_data(self) -> Optional[str]:
        """导出反馈数据为CSV"""
        try:
            feedback_data = st.session_state.get('feedback_data', [])
            if not feedback_data:
                return None

            # 转换为DataFrame
            df = pd.DataFrame(feedback_data)

            # 处理ratings列
            if 'ratings' in df.columns:
                for feedback in feedback_data:
                    if 'ratings' in feedback and feedback['ratings']:
                        for key, value in feedback['ratings'].items():
                            df.loc[df['interaction_id'] ==
                                   feedback['interaction_id'], f'rating_{key}'] = value

            # 转换为CSV
            csv_data = df.to_csv(index=False, encoding='utf-8')
            return csv_data

        except Exception as e:
            print(f"❌ 导出数据失败: {e}")
            return None

    def analyze_feedback_trends(self) -> Optional[Dict]:
        """分析反馈趋势"""
        try:
            feedback_data = st.session_state.get('feedback_data', [])
            if not feedback_data:
                return None

            total_feedback = len(feedback_data)

            # 计算平均评分
            ratings = []
            for feedback in feedback_data:
                if 'average_rating' in feedback:
                    ratings.append(feedback['average_rating'])
                elif 'ratings' in feedback and feedback['ratings']:
                    avg = sum(feedback['ratings'].values()
                              ) / len(feedback['ratings'])
                    ratings.append(avg)

            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            low_rating_count = len([r for r in ratings if r < 3])

            # 改进建议
            improvement_areas = []
            if avg_rating < 3.5:
                improvement_areas.append("整体用户满意度较低，需要提升回答质量")
            if low_rating_count > total_feedback * 0.3:
                improvement_areas.append("低评分反馈较多，建议优化模型参数")

            return {
                'total_feedback': total_feedback,
                'avg_rating': avg_rating,
                'low_rating_count': low_rating_count,
                'improvement_areas': improvement_areas
            }

        except Exception as e:
            print(f"❌ 分析反馈趋势失败: {e}")
            return None


# 创建全局实例
feedback_system = FeedbackSystem()

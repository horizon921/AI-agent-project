import time
import streamlit as st
import json
import os
from datetime import datetime
from typing import List, Dict, Any
import uuid
import pandas as pd
from io import StringIO


class FeedbackSystem:
    def __init__(self):
        self.feedback_file = "feedback_data.json"
        self._init_session_state()

    def _init_session_state(self):
        """初始化 session state"""
        if 'feedback_data' not in st.session_state:
            st.session_state.feedback_data = []
        if 'feedback_stats' not in st.session_state:
            st.session_state.feedback_stats = {}
        if 'interaction_feedback' not in st.session_state:
            st.session_state.interaction_feedback = {}

    def init_session_state(self):
        """公开的初始化方法，供外部调用"""
        self._init_session_state()

    def generate_interaction_id(self) -> str:
        """生成交互ID"""
        return str(uuid.uuid4())

    def display_feedback_widget(self, interaction_id: str, response_content: str):
        """显示反馈组件 - 兼容旧版本"""
        # 🔥 统一使用新的反馈表单
        st.markdown("---")
        with st.expander("📝 为这次回答评分", expanded=False):
            self.show_feedback_form(interaction_id)

    def show_feedback_form(self, interaction_id):
        """显示反馈表单 - 支持分步提交"""
        st.markdown("### 📝 请为这次回答评分")

        # 初始化当前交互的反馈状态
        feedback_key = f"feedback_{interaction_id}"
        if feedback_key not in st.session_state:
            st.session_state[feedback_key] = {
                'ratings': {},
                'comment': '',
                'submitted': False
            }

        current_feedback = st.session_state[feedback_key]

        # 🔥 检查是否已提交
        if current_feedback['submitted']:
            st.success("🎉 感谢您的反馈！您的意见对我们很重要。")

            # 显示提交的评分摘要
            with st.expander("查看已提交的反馈", expanded=False):
                feedback_types = {
                    'accuracy': '准确性',
                    'helpfulness': '有用性',
                    'clarity': '清晰度',
                    'completeness': '完整性',
                    'relevance': '相关性'
                }

                for fb_type, rating in current_feedback['ratings'].items():
                    if rating > 0:
                        fb_name = feedback_types.get(fb_type, fb_type)
                        st.write(f"**{fb_name}**: {'⭐' * rating} ({rating}/5)")

                if current_feedback['comment']:
                    st.write(f"**评论**: {current_feedback['comment']}")
            return

        # 定义反馈类型
        feedback_types = {
            'accuracy': '准确性',
            'helpfulness': '有用性',
            'clarity': '清晰度',
            'completeness': '完整性',
            'relevance': '相关性'
        }

        # 创建两列布局
        col1, col2 = st.columns(2)

        # 评分区域
        with col1:
            st.markdown("**满意度评分**")
            for fb_type, fb_name in feedback_types.items():
                current_rating = current_feedback['ratings'].get(fb_type, 0)
                rating_key = f"rating_{interaction_id}_{fb_type}"

                rating = st.selectbox(
                    fb_name,
                    options=[0, 1, 2, 3, 4, 5],
                    index=current_rating,
                    format_func=lambda x: f"{'⭐' * x} ({x}/5)" if x > 0 else "未评分",
                    key=rating_key
                )

                # 实时更新到session state
                if rating != current_feedback['ratings'].get(fb_type, 0):
                    current_feedback['ratings'][fb_type] = rating
                    st.session_state[feedback_key] = current_feedback

        # 评论区域
        with col2:
            st.markdown("**详细反馈**")
            comment = st.text_area(
                "请提供具体建议（可选）",
                value=current_feedback['comment'],
                height=150,
                key=f"comment_{interaction_id}",
                placeholder="请描述您的具体建议或意见..."
            )

            # 更新评论到session state
            if comment != current_feedback['comment']:
                current_feedback['comment'] = comment
                st.session_state[feedback_key] = current_feedback

        # 显示当前评分状态
        st.markdown("---")
        col3, col4, col5 = st.columns([2, 1, 1])

        with col3:
            # 显示已评分的项目
            rated_items = [name for fb_type, name in feedback_types.items()
                           if current_feedback['ratings'].get(fb_type, 0) > 0]

            if rated_items:
                st.success(f"✅ 已评分: {', '.join(rated_items)}")
            else:
                st.info("💡 请为至少一个维度评分")

        with col4:
            # 提交按钮
            can_submit = any(
                rating > 0 for rating in current_feedback['ratings'].values())

            if st.button(
                "📤 提交反馈",
                key=f"submit_{interaction_id}",
                disabled=not can_submit,
                help="至少需要一个评分才能提交"
            ):
                if self._submit_feedback(interaction_id, current_feedback):
                    current_feedback['submitted'] = True
                    st.session_state[feedback_key] = current_feedback
                    st.success("✅ 反馈提交成功！")
                    st.balloons()
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ 提交失败，请重试")

        with col5:
            # 重置按钮
            if st.button(
                "🔄 重置",
                key=f"reset_{interaction_id}",
                help="清除当前评分"
            ):
                st.session_state[feedback_key] = {
                    'ratings': {},
                    'comment': '',
                    'submitted': False
                }
                st.rerun()

    def _submit_feedback(self, interaction_id, feedback_data):
        """提交反馈数据"""
        try:
            # 计算平均评分
            ratings = feedback_data['ratings']
            valid_ratings = [r for r in ratings.values() if r > 0]
            avg_rating = sum(valid_ratings) / \
                len(valid_ratings) if valid_ratings else 0

            # 构建反馈记录
            feedback_record = {
                'interaction_id': interaction_id,
                'timestamp': datetime.now().isoformat(),
                'ratings': ratings,
                'average_rating': round(avg_rating, 2),
                'comment': feedback_data['comment'],
                'session_id': st.session_state.get('session_id', 'unknown'),
                # 🔥 添加兼容字段
                'rating': round(avg_rating),  # 为了兼容旧统计
                'feedback_type': '多维度评分'
            }

            # 添加到session state
            if 'feedback_data' not in st.session_state:
                st.session_state.feedback_data = []

            st.session_state.feedback_data.append(feedback_record)

            # 标记交互已反馈
            if 'interaction_feedback' not in st.session_state:
                st.session_state.interaction_feedback = {}

            st.session_state.interaction_feedback[interaction_id] = True

            # 保存到文件
            success = self._save_feedback_to_file_single(feedback_record)

            if success:
                self._update_stats()

            return success

        except Exception as e:
            st.error(f"提交反馈时出错: {e}")
            return False

    def save_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """保存反馈数据 - 兼容旧版本"""
        try:
            self._init_session_state()

            # 添加到 session state
            st.session_state.feedback_data.append(feedback_data)

            # 保存到文件
            success = self._save_feedback_to_file_single(feedback_data)

            if success:
                self._update_stats()
                return True
            else:
                st.warning("文件保存失败，但反馈已记录在当前会话中")
                self._update_stats()
                return True

        except Exception as e:
            st.error(f"保存反馈失败: {e}")
            return False

    def _load_feedback_from_file(self) -> List[Dict[str, Any]]:
        """从文件加载反馈数据"""
        try:
            if os.path.exists(self.feedback_file):
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            return []
        except Exception as e:
            st.error(f"读取反馈文件失败: {e}")
            return []

    def _save_feedback_to_file_single(self, feedback_record):
        """保存单个反馈记录到文件"""
        try:
            # 读取现有数据
            existing_data = self._load_feedback_from_file()

            # 检查是否已存在相同的反馈（避免重复）
            interaction_id = feedback_record.get('interaction_id')
            existing_ids = [f.get('interaction_id') for f in existing_data]

            if interaction_id not in existing_ids:
                existing_data.append(feedback_record)

                # 创建备份
                if os.path.exists(self.feedback_file):
                    backup_file = f"{self.feedback_file}.backup"
                    import shutil
                    shutil.copy2(self.feedback_file, backup_file)

                # 保存到文件
                with open(self.feedback_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            st.error(f"保存反馈文件失败: {e}")
            return False

    def get_feedback_stats(self) -> Dict[str, Any]:
        """获取反馈统计"""
        self._init_session_state()

        # 如果 session state 中没有数据，从文件加载
        if not st.session_state.feedback_data:
            st.session_state.feedback_data = self._load_feedback_from_file()
            self._update_stats()

        return st.session_state.feedback_stats

    def _update_stats(self):
        """更新统计信息 - 🔥 修复多维度评分支持"""
        data = st.session_state.feedback_data

        if not data:
            st.session_state.feedback_stats = {
                'total_count': 0,
                'average_rating': 0,
                'rating_distribution': {},
                'feedback_types': {},
                'recent_feedback': []
            }
            return

        # 计算统计信息
        total_count = len(data)
        ratings = []

        # 🔥 处理不同格式的评分数据
        for feedback in data:
            if 'average_rating' in feedback and feedback['average_rating'] > 0:
                # 新格式：多维度评分
                ratings.append(feedback['average_rating'])
            elif 'rating' in feedback and feedback['rating'] > 0:
                # 旧格式：单一评分
                ratings.append(feedback['rating'])

        average_rating = sum(ratings) / len(ratings) if ratings else 0

        # 评分分布
        rating_distribution = {}
        for rating in ratings:
            # 四舍五入到整数
            rounded_rating = round(rating)
            rating_distribution[rounded_rating] = rating_distribution.get(
                rounded_rating, 0) + 1

        # 反馈类型分布
        feedback_types = {}
        for feedback in data:
            fb_type = feedback.get('feedback_type', '未分类')
            feedback_types[fb_type] = feedback_types.get(fb_type, 0) + 1

        # 最近的反馈
        recent_feedback = sorted(data, key=lambda x: x.get(
            'timestamp', ''), reverse=True)[:5]

        st.session_state.feedback_stats = {
            'total_count': total_count,
            'average_rating': average_rating,
            'rating_distribution': rating_distribution,
            'feedback_types': feedback_types,
            'recent_feedback': recent_feedback
        }

    def show_feedback_stats(self):
        """显示反馈统计"""
        self._load_and_merge_feedback_data()
        stats = self.get_feedback_stats()

        if stats['total_count'] == 0:
            st.write("暂无反馈数据")
            return

        # 显示基本统计
        col1, col2 = st.columns(2)
        with col1:
            st.metric("总反馈数", stats['total_count'])
        with col2:
            st.metric("平均评分", f"{stats['average_rating']:.1f}/5")

        # 显示评分分布
        if stats['rating_distribution']:
            st.write("**评分分布:**")
            for rating, count in sorted(stats['rating_distribution'].items()):
                st.write(f"⭐ {rating}星: {count}次")

        # 显示反馈类型分布
        if stats['feedback_types']:
            st.write("**反馈类型:**")
            for fb_type, count in stats['feedback_types'].items():
                st.write(f"• {fb_type}: {count}次")

        # 显示最近反馈
        if stats['recent_feedback']:
            st.write("**最近反馈:**")
            for feedback in stats['recent_feedback'][:3]:
                # 🔥 兼容不同格式
                rating = feedback.get(
                    'average_rating', feedback.get('rating', 0))
                fb_type = feedback.get('feedback_type', '未分类')
                timestamp = feedback.get('timestamp', '')

                if timestamp:
                    try:
                        dt = datetime.fromisoformat(
                            timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime('%m-%d %H:%M')
                    except:
                        time_str = timestamp[:10]
                else:
                    time_str = '未知时间'

                st.write(f"⭐ {rating:.1f}/5 - {fb_type} ({time_str})")

    def _load_and_merge_feedback_data(self):
        """加载并合并所有反馈数据"""
        file_data = self._load_feedback_from_file()
        session_data = st.session_state.get('feedback_data', [])

        all_feedback = []
        seen_ids = set()

        # 先添加文件中的数据
        for feedback in file_data:
            interaction_id = feedback.get('interaction_id')
            if interaction_id and interaction_id not in seen_ids:
                all_feedback.append(feedback)
                seen_ids.add(interaction_id)

        # 再添加session中的新数据
        for feedback in session_data:
            interaction_id = feedback.get('interaction_id')
            if interaction_id and interaction_id not in seen_ids:
                all_feedback.append(feedback)
                seen_ids.add(interaction_id)

        st.session_state.feedback_data = all_feedback

    def analyze_feedback_trends(self) -> Dict[str, Any]:
        """分析反馈趋势"""
        stats = self.get_feedback_stats()

        if stats['total_count'] == 0:
            return {}

        # 分析低评分反馈
        low_rating_count = sum(
            count for rating, count in stats['rating_distribution'].items() if rating <= 2)

        # 生成改进建议
        improvement_areas = []

        if stats['average_rating'] < 3.5:
            improvement_areas.append("整体满意度偏低，需要提升回答质量")

        if low_rating_count > stats['total_count'] * 0.3:
            improvement_areas.append("低评分比例较高，建议优化模型参数")

        # 分析反馈类型
        most_common_issue = max(stats['feedback_types'].items(), key=lambda x: x[1])[
            0] if stats['feedback_types'] else None
        if most_common_issue and stats['feedback_types'][most_common_issue] > stats['total_count'] * 0.4:
            improvement_areas.append(f"'{most_common_issue}'问题较多，需要重点关注")

        return {
            'total_feedback': stats['total_count'],
            'avg_rating': stats['average_rating'],
            'low_rating_count': low_rating_count,
            'improvement_areas': improvement_areas,
            'most_common_issue': most_common_issue
        }

    def export_feedback_data(self) -> str:
        """导出反馈数据为CSV"""
        try:
            self._load_and_merge_feedback_data()
            data = st.session_state.get('feedback_data', [])

            if not data:
                return ""

            df = pd.DataFrame(data)
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8')
            return csv_buffer.getvalue()
        except Exception as e:
            st.error(f"导出数据失败: {e}")
            return ""

    def force_refresh_data(self):
        """强制刷新所有反馈数据"""
        try:
            file_data = self._load_feedback_from_file()
            st.session_state.feedback_data = file_data
            self._update_stats()
            return True
        except Exception as e:
            st.error(f"刷新数据失败: {e}")
            return False


# 创建全局实例
feedback_system = FeedbackSystem()

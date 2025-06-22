# backend/utils/feedback_system.py - 完整修复版本
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
        # 使用绝对路径，确保文件位置可控
        self.data_dir = os.path.join(os.getcwd(), "feedback_data")
        self.data_file = os.path.join(self.data_dir, "feedback_data.json")
        self.feedback_file = self.data_file  # 兼容性别名
        self.backup_file = os.path.join(self.data_dir, "feedback_backup.json")

        # 确保目录存在
        os.makedirs(self.data_dir, exist_ok=True)

        # 显示文件路径（调试用）
        if st.session_state.get('debug_mode', False):
            st.info(f"📁 反馈数据文件路径: {self.feedback_file}")

    def init_session_state(self):
        """初始化 session state - 公开方法"""
        if 'feedback_data' not in st.session_state:
            st.session_state.feedback_data = []
        if 'feedback_stats' not in st.session_state:
            st.session_state.feedback_stats = {}
        if 'interaction_feedback' not in st.session_state:
            st.session_state.interaction_feedback = {}

        # 启动时自动加载文件数据
        self._load_and_sync_data()

    def submit_feedback(self, interaction_id: str, feedback_data: Dict[str, Any]) -> bool:
        """✅ 提交反馈数据 - 主要方法"""
        try:
            # 从 feedback_data 中提取评分
            ratings = feedback_data.get('ratings', {})
            comment = feedback_data.get('comment', '')

            # 计算平均评分
            if ratings:
                avg_rating = sum(ratings.values()) / len(ratings)
            else:
                avg_rating = 3.0  # 默认评分

            # 构建反馈记录
            feedback_record = {
                'interaction_id': interaction_id,
                'timestamp': datetime.now().isoformat(),
                'rating': avg_rating,
                'average_rating': avg_rating,
                'ratings': ratings,  # 保存详细评分
                'comment': comment,
                'session_id': st.session_state.get('session_id', str(uuid.uuid4())),
                'feedback_type': '详细评分'
            }

            # 检查是否已存在相同反馈
            existing_feedback = [
                f for f in st.session_state.feedback_data
                if f.get('interaction_id') == interaction_id
            ]

            if existing_feedback:
                st.warning("该对话已经评过分了")
                return False

            # 添加到session state
            st.session_state.feedback_data.append(feedback_record)

            # 立即保存到文件
            save_success = self._save_feedback_to_file()

            if save_success:
                st.success("✅ 反馈已保存")
            else:
                st.warning("⚠️ 文件保存失败，但反馈已记录在当前会话中")

            # 更新统计
            self._update_stats()

            # 标记为已提交
            st.session_state.interaction_feedback[interaction_id] = True

            return True

        except Exception as e:
            st.error(f"提交反馈时出错: {e}")
            return False

    def _load_and_sync_data(self):
        """加载并同步文件数据到session_state"""
        try:
            file_data = self._load_feedback_from_file()
            if file_data:
                # 合并数据，避免重复
                existing_ids = {f.get('interaction_id')
                                for f in st.session_state.feedback_data}
                new_data = [f for f in file_data if f.get(
                    'interaction_id') not in existing_ids]

                if new_data:
                    st.session_state.feedback_data.extend(new_data)

                self._update_stats()
        except Exception as e:
            st.warning(f"加载历史数据时出错: {e}")

    def show_feedback_form(self, interaction_id):
        """显示反馈表单"""
        st.markdown("### 📝 请为这次回答评分")

        # 检查是否已经提交过反馈
        if self._is_feedback_submitted(interaction_id):
            st.success("🎉 您已经为这次对话评过分了，感谢您的反馈！")
            return

        # 简化的评分界面
        st.markdown("**整体满意度**")
        overall_rating = st.select_slider(
            "请选择整体评分",
            options=[1, 2, 3, 4, 5],
            value=3,
            format_func=lambda x: f"{'⭐' * x} ({x}/5)",
            key=f"overall_rating_{interaction_id}"
        )

        # 可选的详细评论
        comment = st.text_area(
            "详细反馈（可选）",
            placeholder="请描述您的具体建议或意见...",
            height=100,
            key=f"comment_{interaction_id}"
        )

        # 提交按钮
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button(
                "📤 提交评分",
                key=f"submit_{interaction_id}",
                type="primary"
            ):
                success = self._submit_simple_feedback(
                    interaction_id, overall_rating, comment)
                if success:
                    st.success("✅ 反馈提交成功！")
                    st.balloons()
                    st.session_state.interaction_feedback[interaction_id] = True
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ 提交失败，请重试")

        with col2:
            if st.button("🔄 重置", key=f"reset_{interaction_id}"):
                st.rerun()

        with col3:
            st.info(f"当前评分: {'⭐' * overall_rating}")

    def _submit_simple_feedback(self, interaction_id: str, rating: int, comment: str) -> bool:
        """提交简化的反馈数据"""
        try:
            feedback_record = {
                'interaction_id': interaction_id,
                'timestamp': datetime.now().isoformat(),
                'rating': rating,
                'average_rating': rating,
                'comment': comment,
                'session_id': st.session_state.get('session_id', str(uuid.uuid4())),
                'feedback_type': '整体评分'
            }

            # 检查是否已存在相同反馈
            existing_feedback = [
                f for f in st.session_state.feedback_data
                if f.get('interaction_id') == interaction_id
            ]

            if existing_feedback:
                st.warning("该对话已经评过分了")
                return False

            # 添加到session state
            st.session_state.feedback_data.append(feedback_record)

            # 立即保存到文件
            self._save_feedback_to_file()

            # 更新统计
            self._update_stats()

            return True

        except Exception as e:
            st.error(f"提交反馈时出错: {e}")
            return False

    def _is_feedback_submitted(self, interaction_id: str) -> bool:
        """检查是否已提交反馈"""
        if st.session_state.interaction_feedback.get(interaction_id):
            return True

        existing_feedback = [
            f for f in st.session_state.feedback_data
            if f.get('interaction_id') == interaction_id
        ]

        if existing_feedback:
            st.session_state.interaction_feedback[interaction_id] = True
            return True

        return False

    def _save_feedback_to_file(self) -> bool:
        """保存所有反馈数据到文件"""
        try:
            data = st.session_state.feedback_data

            # 创建备份
            if os.path.exists(self.feedback_file):
                import shutil
                shutil.copy2(self.feedback_file, self.backup_file)

            # 保存到主文件
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            st.error(f"保存反馈文件失败: {e}")
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
            st.warning(f"读取反馈文件失败: {e}")
            return []

    def _update_stats(self):
        """更新统计信息"""
        data = st.session_state.feedback_data

        if not data:
            st.session_state.feedback_stats = {
                'total_count': 0,
                'average_rating': 0,
                'rating_distribution': {},
                'recent_feedback': []
            }
            return

        # 计算统计信息
        total_count = len(data)
        ratings = [f.get('rating', f.get('average_rating', 0))
                   for f in data if f.get('rating', f.get('average_rating', 0)) > 0]

        average_rating = sum(ratings) / len(ratings) if ratings else 0

        # 评分分布
        rating_distribution = {}
        for rating in ratings:
            rounded_rating = round(rating)
            rating_distribution[rounded_rating] = rating_distribution.get(
                rounded_rating, 0) + 1

        # 最近的反馈
        recent_feedback = sorted(data, key=lambda x: x.get(
            'timestamp', ''), reverse=True)[:5]

        st.session_state.feedback_stats = {
            'total_count': total_count,
            'average_rating': average_rating,
            'rating_distribution': rating_distribution,
            'recent_feedback': recent_feedback
        }

    def show_feedback_stats(self):
        """显示反馈统计"""
        stats = st.session_state.feedback_stats

        if stats.get('total_count', 0) == 0:
            st.info("📊 暂无反馈数据")
            return

        # 显示基本统计
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("总反馈数", stats['total_count'])

        with col2:
            avg_rating = stats.get('average_rating', 0)
            st.metric("平均评分", f"{avg_rating:.1f}⭐")

        with col3:
            distribution = stats.get('rating_distribution', {})
            satisfied = distribution.get(4, 0) + distribution.get(5, 0)
            total = stats.get('total', 0)

            if total > 0:
                rate = round((satisfied / total) * 100, 1)
                st.metric("满意度", f"{rate:.1f}%")
            else:
                st.metric("满意度", "0%")

        # 显示评分分布
        if stats.get('rating_distribution'):
            st.markdown("#### 📊 评分分布")
            for rating in range(5, 0, -1):
                count = stats['rating_distribution'].get(rating, 0)
                percentage = (
                    count / stats['total_count'] * 100) if stats['total_count'] > 0 else 0
                st.write(f"{'⭐' * rating}: {count}次 ({percentage:.1f}%)")

    def force_refresh_data(self):
        """强制刷新数据"""
        self._load_and_sync_data()

    def export_feedback_data(self) -> str:
        """导出反馈数据为CSV格式"""
        try:
            data = st.session_state.feedback_data
            if not data:
                return ""

            # 转换为DataFrame
            df = pd.DataFrame(data)

            # 转换为CSV字符串
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8')
            return csv_buffer.getvalue()

        except Exception as e:
            st.error(f"导出数据失败: {e}")
            return ""

    def analyze_feedback_trends(self) -> Dict[str, Any]:
        """分析反馈趋势"""
        data = st.session_state.feedback_data
        if not data:
            return {}

        # 计算基本统计
        total_feedback = len(data)
        ratings = [f.get('rating', f.get('average_rating', 0))
                   for f in data if f.get('rating', f.get('average_rating', 0)) > 0]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        low_rating_count = len([r for r in ratings if r < 3])

        # 生成改进建议
        improvement_areas = []
        if avg_rating < 3.5:
            improvement_areas.append("整体评分偏低，需要提升回答质量")
        if low_rating_count > total_feedback * 0.3:
            improvement_areas.append("低评分比例较高，需要重点关注用户不满意的原因")

        return {
            'total_feedback': total_feedback,
            'avg_rating': avg_rating,
            'low_rating_count': low_rating_count,
            'improvement_areas': improvement_areas
        }


# 创建全局实例
feedback_system = FeedbackSystem()

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status

import random

from user.models import Skills, UserProfile
from project.models import Comment, Project

from .serializers import UserProfileSkillsSerializer, RecommendProjectsSerializer
from .ai import user_based 

from _utils.query_utils import query_debugger # Query Debugger

# userprofile 업데이트 하면 추천 리스트 업데이트
class RecommendView(APIView):
    @query_debugger
    def get(self, request):
        # 1. 추천 시스템 최초 요청
        # userinfo = UserProfile.objects.all() # (user = request.user)
        # result = UserSkillsSerializer(userinfo, many=True).data

        # userinfo = UserProfile.objects.all()
        userinfo = UserProfile.objects.select_related('user').prefetch_related('skills').all()
        # userinfo = UserProfile.objects.select_related('user').all() # .prefetch_related('skills').all()

        result = UserProfileSkillsSerializer(userinfo, many=True).data

        # 2. 기본 Base DF 만들기 (USER별 SKILLS 반영)
        base_df = user_based.make_df(result)

        # 3. 코사인 유사도 구하기 + 가장 높은 User 2~5명의 Project 전부 출력
        user_id_list, jaccard_score_dict = user_based.get_jaccard_score_user_id_list(base_df, request.user.id)
        print(user_id_list, jaccard_score_dict)

        # 4. 최종 user들의 project 가져오기
        project_querysets = Project.objects.filter(user__in = user_id_list)
        project_querysets_list = list(project_querysets)
        print(project_querysets_list)

        # 5. User들의 Project 중 랜덤 추출
        if len(project_querysets_list) >=3:
            project_querysets_random3_list = random.sample(project_querysets_list, 3)
            # print('1', project_querysets_random3_list)
        else:
            project_querysets = Project.objects.exclude(user = request.user.id)
            project_querysets_list = list(project_querysets)
            project_querysets_random3_list = random.sample(project_querysets_list, 3)
            # print('2', project_querysets_random3_list)

        # # 6. Serializers 결과 조회.
        rec_result_projects_data = RecommendProjectsSerializer(project_querysets_random3_list, many=True).data
        # return Response(result, status=status.HTTP_200_OK)
        return Response({'results':rec_result_projects_data, 'scores':jaccard_score_dict}, status=status.HTTP_200_OK)
    
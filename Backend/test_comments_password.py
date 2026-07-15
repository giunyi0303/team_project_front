import unittest

from fastapi.testclient import TestClient

import main


class CommentPasswordTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)

    def test_comment_creation_requires_password(self):
        create_response = self.client.post(
            "/api/posts",
            json={"title": "테스트 글", "content": "테스트 내용", "password": "1234"},
        )
        self.assertEqual(create_response.status_code, 201)
        post_id = create_response.json()["id"]

        response = self.client.post(
            f"/api/posts/{post_id}/comments",
            json={"content": "비밀번호 없는 답글"},
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()

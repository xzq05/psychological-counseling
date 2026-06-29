# app/api/posts.py
from fastapi import APIRouter, HTTPException, Form, Query
from fastapi.responses import JSONResponse
from app.database import get_db
from bson import ObjectId
import re
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/posts", tags=["帖子"])


def is_valid_object_id(id_str):
    if not id_str:
        return False
    return bool(re.match(r'^[0-9a-fA-F]{24}$', id_str))


def get_beijing_time():
    return datetime.utcnow() + timedelta(hours=8)


def serialize_doc(doc):
    if doc:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        for key, value in doc.items():
            if isinstance(value, datetime):
                doc[key] = value.isoformat()
            elif isinstance(value, ObjectId):
                doc[key] = str(value)
    return doc


@router.get("")
async def get_all_posts():
    try:
        db = get_db()
        cursor = db["posts"].find().sort("created_at", -1)
        posts = []
        async for doc in cursor:
            doc = serialize_doc(doc)
            posts.append(doc)
        return JSONResponse(
            status_code=200,
            content={"success": True, "data": posts}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"获取帖子失败: {str(e)}"}
        )


@router.get("/{post_id}")
async def get_post_detail(post_id: str):
    try:
        if not is_valid_object_id(post_id):
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "无效的帖子ID"}
            )
        db = get_db()
        post = await db["posts"].find_one({"_id": ObjectId(post_id)})
        if not post:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "帖子不存在"}
            )
        post = serialize_doc(post)
        return JSONResponse(
            status_code=200,
            content={"success": True, "data": post}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"获取帖子失败: {str(e)}"}
        )


@router.post("")
async def create_post(
        title: str = Form(...),
        content: str = Form(...),
        category: str = Form("其他"),
        author: str = Form(...),
        author_id: str = Form(...)
):
    try:
        db = get_db()
        post = {
            "title": title,
            "content": content,
            "category": category,
            "author": author,
            "author_id": author_id,
            "likes": 0,
            "comments": [],
            "comments_count": 0,
            "created_at": get_beijing_time(),
            "updated_at": get_beijing_time()
        }
        result = await db["posts"].insert_one(post)
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "帖子发布成功", "id": str(result.inserted_id)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"发布帖子失败: {str(e)}"}
        )


@router.put("/{post_id}")
async def update_post(
        post_id: str,
        title: str = Form(...),
        content: str = Form(...),
        category: str = Form("其他"),
        author_id: str = Form(...)
):
    try:
        if not is_valid_object_id(post_id):
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "无效的帖子ID"}
            )

        db = get_db()
        post = await db["posts"].find_one({"_id": ObjectId(post_id)})
        if not post:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "帖子不存在"}
            )

        if post.get("author_id") != author_id:
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "只能修改自己的帖子"}
            )

        await db["posts"].update_one(
            {"_id": ObjectId(post_id)},
            {"$set": {
                "title": title,
                "content": content,
                "category": category,
                "updated_at": get_beijing_time()
            }}
        )
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "帖子修改成功"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"修改帖子失败: {str(e)}"}
        )


@router.delete("/{post_id}")
async def delete_post(
        post_id: str,
        author_id: str = Query(...)
):
    try:
        if not is_valid_object_id(post_id):
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "无效的帖子ID"}
            )

        db = get_db()
        post = await db["posts"].find_one({"_id": ObjectId(post_id)})
        if not post:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "帖子不存在"}
            )

        if post.get("author_id") != author_id:
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "只能删除自己的帖子"}
            )

        await db["posts"].delete_one({"_id": ObjectId(post_id)})
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "帖子删除成功"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"删除帖子失败: {str(e)}"}
        )


@router.post("/{post_id}/like")
async def like_post(post_id: str):
    try:
        if not is_valid_object_id(post_id):
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "无效的帖子ID"}
            )
        db = get_db()
        result = await db["posts"].update_one(
            {"_id": ObjectId(post_id)},
            {"$inc": {"likes": 1}}
        )
        if result.modified_count == 0:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "帖子不存在"}
            )
        post = await db["posts"].find_one({"_id": ObjectId(post_id)})
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "点赞成功", "likes": post.get("likes", 0)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"点赞失败: {str(e)}"}
        )


@router.post("/{post_id}/comment")
async def add_comment(
        post_id: str,
        comment_author: str = Form(...),
        comment_author_id: str = Form(...),
        comment_content: str = Form(...)
):
    try:
        if not is_valid_object_id(post_id):
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "无效的帖子ID"}
            )
        db = get_db()

        comment = {
            "id": str(ObjectId()),
            "author": comment_author,
            "author_id": comment_author_id,
            "content": comment_content,
            "created_at": get_beijing_time().isoformat()
        }

        result = await db["posts"].update_one(
            {"_id": ObjectId(post_id)},
            {
                "$push": {"comments": comment},
                "$inc": {"comments_count": 1}
            }
        )

        if result.modified_count == 0:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "帖子不存在"}
            )

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "评论成功", "comment": comment}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"评论失败: {str(e)}"}
        )


@router.delete("/{post_id}/comment/{comment_id}")
async def delete_comment(
        post_id: str,
        comment_id: str,
        author_id: str = Query(...)
):
    try:
        if not is_valid_object_id(post_id):
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "无效的帖子ID"}
            )

        db = get_db()
        post = await db["posts"].find_one({"_id": ObjectId(post_id)})
        if not post:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "帖子不存在"}
            )

        comment_to_delete = None
        for c in post.get("comments", []):
            if c.get("id") == comment_id:
                comment_to_delete = c
                break

        if not comment_to_delete:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "评论不存在"}
            )

        if comment_to_delete.get("author_id") != author_id:
            return JSONResponse(
                status_code=403,
                content={"success": False, "message": "只能删除自己的评论"}
            )

        await db["posts"].update_one(
            {"_id": ObjectId(post_id)},
            {
                "$pull": {"comments": {"id": comment_id}},
                "$inc": {"comments_count": -1}
            }
        )

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "评论已删除"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"删除评论失败: {str(e)}"}
        )
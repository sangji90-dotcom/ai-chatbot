class Character {
  final String id;
  final String name;
  final String description;
  final String imageUrl;
  final String firstMessage;
  final int likeCount;
  final int chatCount;
  final int viewCount;
  final List<String> tags;

  Character({
    required this.id,
    required this.name,
    required this.description,
    required this.imageUrl,
    required this.firstMessage,
    required this.likeCount,
    required this.chatCount,
    required this.viewCount,
    required this.tags,
  });

  factory Character.fromJson(Map<String, dynamic> json) {
    return Character(
      id: json['id'] ?? '',
      name: json['name'] ?? '',
      description: json['description'] ?? '',
      imageUrl: json['image_url'] ?? '',
      firstMessage: json['first_message'] ?? '',
      likeCount: json['like_count'] ?? 0,
      chatCount: json['chat_count'] ?? 0,
      viewCount: json['view_count'] ?? 0,
      tags: List<String>.from(json['tags'] ?? []),
    );
  }
}
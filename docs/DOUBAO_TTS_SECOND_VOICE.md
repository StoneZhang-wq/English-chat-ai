# 豆包 TTS 开通第二个音色（双人声）操作指南

当前项目用豆包 TTS 时，**角色 A（NPC）** 与 **角色 B（用户）** 可配置不同人声。若未开通第二个音色，B 会报错 `45000030 / requested resource not granted`，此时程序已做回退：B 自动使用 A 的人声。

若要 **真正使用两个不同人声**（如女声 + 男声），需在火山引擎侧开通第二个音色。

---

## 一、登录控制台

1. 打开 **火山引擎控制台**：<https://console.volcengine.com/>
2. 使用你的账号登录（与当前 `VOLCENGINE_APP_ID` / `VOLCENGINE_ACCESS_TOKEN` 对应的账号）。

---

## 二、进入豆包语音

1. 在控制台顶栏或产品列表中找到 **「智能语音」** 或 **「豆包语音」**。
2. 进入 **豆包语音** 产品页。
3. 在左侧菜单找到与 **「语音合成」**、**「大模型语音合成」** 或 **「音色 / 资源包」** 相关的入口。

---

## 三、查看 / 开通音色

豆包语音下通常有两种与“第二个音色”相关的能力：

### 方式 1：大模型音色（你当前用的类型）

- 你当前使用的 `zh_female_cancan_mars_bigtts`、`zh_male_chunhou_mars_bigtts` 属于 **大模型语音合成** 的 `volcano_tts` 音色。
- 在控制台中查找：
  - **「语音合成大模型」** → **「音色列表」** 或 **「资源包」**；
  - 或 **「服务开通」** / **「开通服务」** 中是否有按音色或按资源包开通的选项。
- 文档参考（音色列表）：  
  <https://www.volcengine.com/docs/6561/1257544>  
- 若控制台有 **「购买资源包」** 或 **「开通音色」**：
  - 选择你需要的**第二个音色**（如男声 `zh_male_chunhou_mars_bigtts` 或列表中其他已开放音色）；
  - 按页面提示完成开通/购买。

### 方式 2：音色下单 API（声音复刻等）

- 文档中有 **OrderAccessResourcePacks（音色下单）**、**OrderResourcePacks（购买资源包）** 等接口，用于购买/开通额外音色或资源包。
- 若控制台没有明显“第二个音色”开关，可能是通过 **「资源包」** 或 **「音色下单」** 开通：
  - 在豆包语音控制台找 **「资源包」**、**「音色管理」** 或 **「购买/下单」**；
  - 或联系火山引擎客服/商务，说明需要再开通一个 **大模型 TTS 音色**（与当前 `zh_female_cancan_mars_bigtts` 区分使用的第二个人声）。

---

## 四、开通后在本项目中的配置

1. 在火山引擎控制台或文档中确认你**新开通的音色名称**（如 `zh_male_xxx_mars_bigtts`）。
2. 在项目根目录的 **`.env`** 中取消注释并填写 B 人声（第二个音色）：

```env
# 角色 A（NPC）人声
TTS_VOICE_TYPE=zh_female_cancan_mars_bigtts

# 角色 B（用户）人声：填你新开通的音色名
TTS_VOICE_TYPE_B=zh_male_chunhou_mars_bigtts
```

3. 若不确定音色名，可查文档 **「音色列表」**：  
   <https://www.volcengine.com/docs/6561/1257544>  
   或 **「ListBigModelTTSTimbres - 大模型音色列表」**：  
   <https://www.volcengine.com/docs/6561/1770994>

4. 保存 `.env` 后重启应用；若 B 人声仍不可用，程序会自动回退为 A 人声，不会报错。

---

## 五、若控制台找不到入口

- 查看 **控制台使用 FAQ**：<https://www.volcengine.com/docs/6561/196768>
- 或通过火山引擎官网 **工单/客服** 咨询：  
  “需要为豆包语音大模型 TTS 再开通一个音色（与现有 zh_female_cancan_mars_bigtts 区分），应如何在控制台操作或通过哪个接口开通？”

---

## 六、参考文档汇总

| 说明           | 链接 |
|----------------|------|
| 豆包语音文档首页 | https://www.volcengine.com/docs/6561 |
| 快速入门（新版控制台） | https://www.volcengine.com/docs/6561/2119699 |
| 音色列表（语音合成大模型） | https://www.volcengine.com/docs/6561/1257544 |
| 大模型音色列表 API | https://www.volcengine.com/docs/6561/1770994 |
| 开通服务 ActivateService | https://www.volcengine.com/docs/6561/1801944 |
| 购买资源包 OrderResourcePacks | https://www.volcengine.com/docs/6561/1801940 |
| 音色下单 OrderAccessResourcePacks | https://www.volcengine.com/docs/6561/1801954 |

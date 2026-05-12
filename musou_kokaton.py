import math
import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100
HEIGHT = 650
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    delta = {
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)
        self.imgs = {
            (+1, 0): img,
            (+1, -1): pg.transform.rotozoom(img, 45, 0.9),
            (0, -1): pg.transform.rotozoom(img, 90, 0.9),
            (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),
            (-1, 0): img0,
            (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),
            (0, +1): pg.transform.rotozoom(img, -90, 0.9),
            (+1, +1): pg.transform.rotozoom(img, -45, 0.9),
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        # 【追加機能4：無敵状態用変数】---------------------------
        self.state = "normal"      # 通常状態 or 無敵状態("hyper")
        self.hyper_life = 0        # 無敵時間の残りフレーム数
        # ------------------------------------------------------

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(
            pg.image.load(f"fig/{num}.png"), 0, 0.9)
        self.image = pg.transform.rotozoom(
            pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        # 【追加機能4：無敵状態の画像変換と時間管理】-------------
        if self.state == "hyper":
            self.image = pg.transform.laplacian(self.image) # ラプラシアン変換適用
            self.hyper_life -= 1
            if self.hyper_life < 0:
                self.state = "normal"  # 500フレーム経過で元に戻る
        # ------------------------------------------------------
        screen.blit(self.image, self.rect)


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255),
              (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255),
              (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        super().__init__()
        rad = random.randint(10, 50)
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = 6
        self.state = "active"

    def update(self):
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


#追加機能６：弾幕
class NeoBeam(pg.sprite.Sprite):
    def __init__(self, bird: Bird, num: int):
        super().__init__()
        self.num = num
    
    def gen_beams(self):
        self.step = 100 // (self.num - 1)
        self.bms = []
        for i in range(-50, +51, self.step):
            self.bms.append(i)
        return self.bms
    

class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird, angle0: 0):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle+angle0, 1.0)
        self.vx = math.cos(math.radians(angle+angle0))
        self.vy = -math.sin(math.radians(angle+angle0))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """

    def __init__(self, obj: "Bomb|Enemy", life: int):
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        self.life -= 1
        self.image = self.imgs[self.life//10 % 2]
        self.image = self.imgs[self.life//10 % 2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]

    def __init__(self):
        super().__init__()
        self.image = pg.transform.rotozoom(
            random.choice(__class__.imgs), 0, 0.8)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vx, self.vy = 0, +6
        self.bound = random.randint(50, HEIGHT//2)
        self.state = "down"
        self.interval = random.randint(50, 300)

    def update(self):
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)

# 🛡 防御壁クラス（追加）


class Shield(pg.sprite.Sprite):  # ← 追加
    def __init__(self, bird: Bird, life: int):
        super().__init__()
        w, h = 20, bird.rect.height * 2
        self.image = pg.Surface((w, h))
        pg.draw.rect(self.image, (0, 0, 255), (0, 0, w, h))
        self.image.set_colorkey((0, 0, 0))

        vx, vy = bird.dire
        angle = math.degrees(math.atan2(-vy, vx))
        self.image = pg.transform.rotozoom(self.image, angle, 1.0)

        self.rect = self.image.get_rect()
        self.rect.centerx = bird.rect.centerx + bird.rect.width * vx
        self.rect.centery = bird.rect.centery + bird.rect.height * vy

        self.life = life

    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill()

class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """

    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)
        

#追加機能２：重力場
class Gravity(pg.sprite.Sprite):
    """
    重力場に関するクラス
    スコア200消費
    """
    def __init__(self,life:int):
        super().__init__()
        self.image = pg.Surface((WIDTH,HEIGHT))
        pg.draw.rect(self.image,((0,0,0)),pg.Rect(0,0,WIDTH, HEIGHT))
        self.image.set_alpha(200)
        self.rect = self.image.get_rect()
        self.rect.center = [WIDTH/2,HEIGHT/2]
        self.life = life
        
    def update(self, exps, emys, bombs, gravs):
        for emy in pg.sprite.groupcollide(emys, gravs, True, False).keys():  # ビームと衝突した敵機リスト
            exps.add(Explosion(emy, 100))
        for bomb in pg.sprite.groupcollide(bombs, gravs, True, False).keys():  # ビームと衝突した爆弾リスト
            exps.add(Explosion(bomb, 50)) 
        self.life -= 1
        if self.life < 0:
            self.kill()


class EMP(pg.sprite.Sprite):
    def __init__(self, emys: pg.sprite.Group, bombs: pg.sprite.Group):
        super().__init__()
        self.image = pg.Surface((WIDTH, HEIGHT))
        pg.draw.rect(self.image, (255, 255, 0), (0, 0, WIDTH, HEIGHT))
        self.image.set_alpha(128)
        self.rect = self.image.get_rect()
        self.life = 3

        for emy in emys.sprites():
            emy.interval = math.inf          # 爆弾を撃てなくする
            emy.image = pg.transform.laplacian(emy.image)  # 見た目変える

        for bomb in bombs.sprites():
            bomb.speed /= 2                  # 速度半分
            bomb.state = "inactive"          # 無効化

    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill()

class Life:
    """
    こうかとんの残機数を表示するクラス
    """
    def __init__(self, num: int):
        self.value = num  # 残機数
        self.size = 40    # ハート1個のサイズ

        # ハート画像を作る
        self.image = pg.Surface((self.size, self.size))
        self.image.set_colorkey((0, 0, 0))

        # ハートの描画
        points = [
            (16*math.sin(t/100)**3 + 20,
             -(13*math.cos(t/100) - 5*math.cos(2*t/100)
               - 2*math.cos(3*t/100) - math.cos(4*t/100)) + 20)
            for t in range(0, 628)
        ]
        pg.draw.polygon(self.image, (255, 0, 0), points)

    def update(self, screen: pg.Surface):
        # 右下にハートを value 個並べて描画
        for i in range(self.value):
            x = WIDTH - 50 - i * (self.size + 10)
            y = HEIGHT - 50
            rect = self.image.get_rect(center=(x, y))
            screen.blit(self.image, rect)

def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()
    life = Life(3) #残機数を3に設定
    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    emps = pg.sprite.Group()
    shields = pg.sprite.Group()  # 追加
    gravs = pg.sprite.Group() #追加機能２：重力場

    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
           
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                if key_lst[pg.K_1]:
                    for i in NeoBeam(bird, 5).gen_beams():
                        beams.add(Beam(bird, i))
                else:
                    beams.add(Beam(bird, 0))
                # 【追加機能4：無敵発動条件（右Shiftかつスコア100より大）】
                if event.key == pg.K_RSHIFT and score.value > 100:
                    bird.state = "hyper"
                    bird.hyper_life = 500
                    score.value -= 100  # 消費スコア100
                # ------------------------------------------------------
            if event.type == pg.KEYDOWN and event.key == pg.K_e:
                if score.value > 20:
                    emps.add(EMP(emys, bombs))
                    score.value -= 20

            #  sキーで防御壁発動（追加）
            if event.type == pg.KEYDOWN and event.key == pg.K_s:
                if score.value >= 50 and len(shields) == 0:
                    shields.add(Shield(bird, 400))
                    score.value -= 50

            #追加機能2：重力場
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN and score.value >= 200:
                gravs.add(Gravity(400))
                score.value -= 200 # スコア200消費
        screen.blit(bg_img, [0, 0])

        if tmr % 200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())

        for emy in emys:
            # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
            if emy.state == "stop" and tmr % emy.interval == 0:
                bombs.add(Bomb(emy, bird))

        # ビームと衝突した敵機リスト
        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト
        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))
            score.value += 10
            bird.change_img(6, screen)

        # ビームと衝突した爆弾リスト
        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ
        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))
            score.value += 1

        # 【追加機能4：こうかとんと爆弾の衝突判定を拡張】-----------
        for bomb in pg.sprite.spritecollide(bird, bombs, True):
            if bomb.state == "inactive":  # 無効化された爆弾はスルー
                continue

            if bird.state == "hyper":
                # 無敵状態なら死なずに爆弾を爆発させ、スコアを1アップ
                exps.add(Explosion(bomb, 50))
                score.value += 1
                continue

                # 通常状態ならゲームオーバー
            bird.change_img(8, screen)
            life.value -= 1 #残機を1減らす

            if life.value <= 0:
                score.update(screen)
                life.update(screen)
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
            
        # ------------------------------------------------------
        #  防御壁と爆弾の衝突処理（追加）

        for bomb in pg.sprite.groupcollide(bombs, shields, True, False).keys():
            exps.add(Explosion(bomb, 50))
            score.value += 1

        gravs.update(exps, emys, bombs, gravs) #追加機能２：重力場
        gravs.draw(screen) #追加機能２：重力場
        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        shields.update()      # 追加
        shields.draw(screen)  # 追加
        exps.update()
        exps.draw(screen)
        score.update(screen)
        emps.update()
        emps.draw(screen)
        life.update(screen) 
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()

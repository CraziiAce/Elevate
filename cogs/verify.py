import discord
import random
import asyncio
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
from pymongo import MongoClient


class verify(commands.Cog):
    """Keep your server safe with a simple captcha"""

    def __init__(self, bot):
        self.bot = bot
        mcl = MongoClient()
        self.data = mcl.Elevate.verify
        self.color = bot.color
        self.footer = bot.footer

    async def make_img(self):
        image = Image.open("imgen/blue.png")
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("imgen/Helvetica.ttf", size=40)
        (x, y) = (452, 230)
        num1 = random.randint(1, 11)
        num2 = random.randint(1, 11)
        message = f"{num1} + {num2}"
        color = "rgb(255, 255, 255)"  # font color
        draw.text((x, y), message, fill=color, font=font)
        image.save("imgen/verify.png")
        return num1 + num2

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def verifyset(self, ctx):
        """Change verification settings"""
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @verifyset.command()
    async def role(self, ctx, role: discord.Role = None):
        """Set the verify role"""
        doc = self.data.find_one({"_id": ctx.guild.id})
        if not doc:
            if role and not doc:
                self.data.insert_one({"_id": ctx.guild.id, "role": role.id})
                await ctx.send(f"Successfully set the verify role to {role.mention}")
                return
            elif not role:
                await ctx.send("You didn't specify a role!")
                return
        elif doc:
            if not role and not doc.get("role"):
                await ctx.send("You didn't specify a role!")
                return
            elif not role and doc.get("role"):
                self.data.update_one(
                    filter={"_id": ctx.guild.id}, update={"$unset": {"role": ""}}
                )
                await ctx.send("Role cleared")
                return
            else:
                self.data.update_one(
                    filter={"_id": ctx.guild.id}, update={"$set": {"role": role.id}}
                )
                await ctx.send(f"Successfully set the verify role to {role.mention}")
                return
        else:
            await ctx.send(
                f"Sorry, but I encountered an unexpected error. Please contact support with `{ctx.prefix}supportrequest`"
            )

    @commands.command()
    @commands.cooldown(1, 300, commands.BucketType.member)
    async def verify(self, ctx):
        """Verify yourself"""
        doc = self.data.find_one({"_id": ctx.guild.id})
        if not doc:
            return await ctx.send("The server admins have not set this feature up!")
        role = ctx.guild.get_role(doc.get("role"))
        if not role:
            return await ctx.send(
                "This server's admins have not set verification up yet!"
            )
        if role in ctx.author.roles:
            await ctx.send("You are already verified!")
        else:
            ans = await self.make_img()
            file = discord.File("imgen/verify.png", filename="verify.png")
            emb = discord.Embed(
                title="Verification",
                description="You need to solve an easy captcha to get access to this server! What is the answer to the addition problem above?",
                color=self.color,
            )
            emb.set_footer(text=self.footer)
            emb.set_image(url="attachment://image.png")
            await ctx.send(file=file, embed=emb)
            try:
                user_ans = await self.bot.wait_for(
                    "message",
                    timeout=60.0,
                    check=lambda m: (
                        ctx.author == m.author and ctx.channel == m.channel
                    ),
                )
            except asyncio.TimeoutError:
                return await ctx.send("Timed out")
            if str(user_ans.content) == str(ans):
                await ctx.author.add_roles(role, reason="Verified")
                await ctx.send("Correct! You have been verified!")
            else:
                await ctx.send("Sorry, but that is wrong.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        doc = self.data.find_one({"_id": member.guild.id})
        if doc.get("do") and doc.get("automatic"):
            chnl = self.bot.get_channel(doc.get("chnl"))
            emb = discord.Embed(
                title="Verification",
                description="You need to solve an easy captcha to get access to this server! What is the answer to the addition problem above?",
                color=self.color,
            )
            await chnl.send(member.mention, embed=emb)


def setup(bot):
    bot.add_cog(verify(bot))
